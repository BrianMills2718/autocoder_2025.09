from autocoder_cc.observability.structured_logging import get_logger
#!/usr/bin/env python3
"""
Query Handler Component
======================

Base class for handling queries (read operations) in CQRS architecture.
Queries read from optimized read stores (Redis projections) and return data.

Implements Step 6 of Enterprise Roadmap v2: Full CQRS implementation.
"""
import anyio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from autocoder_cc.components.composed_base import ComposedComponent


class QueryHandler(ComposedComponent):
    """
    Base class for handling queries (read operations).
    
    Queries are processed through this handler which:
    1. Validates the query
    2. Reads from Redis or read-optimized store
    3. Returns projection data
    4. Does NOT modify state (queries are read-only)
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.component_type = "QueryHandler"
        
        # Redis configuration for read models using generator_settings
        from autocoder_cc.generators.config import generator_settings
        self.redis_url = config.get('redis_url', generator_settings.get_redis_url())
        self.redis_key_prefix = config.get('redis_key_prefix', f'{name}:')
        self.cache_ttl = config.get('cache_ttl', 3600)  # 1 hour default
        
        # Statistics
        self.queries_processed = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        self.logger = get_logger(f"QueryHandler.{self.name}")
    
    async def process(self) -> None:
        """Process queries from input streams"""
        try:
            # Connect to Redis for read models
            import aioredis
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding='utf-8',
                decode_responses=True
            )
            
            self.logger.info(f"QueryHandler {self.name} connected to Redis")
            
            # Process queries from input streams
            async for query_data in self.receive_streams['queries']:
                result = await self._handle_query(query_data)
                
                # Send result to output stream
                await self.send_streams['results'].send(result)
                
        except Exception as e:
            self.logger.error(f"QueryHandler {self.name} failed: {e}")
            raise
        finally:
            if hasattr(self, 'redis'):
                await self.redis.close()
    
    async def _handle_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a single query"""
        query_id = query_data.get('query_id', f"qry_{anyio.get_cancelled_exc_class().time()}")
        query_type = query_data.get('query_type', 'unknown')
        
        try:
            self.logger.info(f"Processing query {query_id} of type {query_type}")
            
            # Validate query
            validation_result = await self._validate_query(query_data)
            if not validation_result['valid']:
                self.queries_processed += 1
                return {
                    'query_id': query_id,
                    'success': False,
                    'error': validation_result['error'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Execute query
            result = await self._execute_query(query_data)
            
            self.queries_processed += 1
            self.logger.info(f"Query {query_id} processed successfully")
            
            return {
                'query_id': query_id,
                'query_type': query_type,
                'success': True,
                'data': result.get('data', {}),
                'metadata': result.get('metadata', {}),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error handling query {query_id}: {e}")
            self.queries_processed += 1
            return {
                'query_id': query_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _validate_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate query data.
        Override in subclasses for specific validation logic.
        """
        # Basic validation
        required_fields = ['query_type']
        for field in required_fields:
            if field not in query_data:
                return {'valid': False, 'error': f"Missing required field: {field}"}
        
        return {'valid': True}
    
    async def _execute_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute query business logic.
        MUST be overridden in subclasses with actual implementation.
        """
        query_type = query_data.get('query_type')
        query_params = query_data.get('params', {})
        
        # Try to get data from cache first
        cache_key = self._build_cache_key(query_type, query_params)
        cached_data = await self._get_from_cache(cache_key)
        
        if cached_data is not None:
            self.cache_hits += 1
            self.logger.debug(f"Cache hit for query {query_type}")
            return {
                'data': cached_data,
                'metadata': {
                    'source': 'cache',
                    'cache_key': cache_key
                }
            }
        
        self.cache_misses += 1
        
        # Default implementation - subclasses should override
        self.logger.warning(f"Default query execution for {query_type} - should be overridden")
        
        # Generate default response
        result_data = {
            'query_type': query_type,
            'params': query_params,
            'message': 'Default query response - implement _execute_query in subclass',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache the result
        await self._set_cache(cache_key, result_data)
        
        return {
            'data': result_data,
            'metadata': {
                'source': 'computed',
                'cache_key': cache_key
            }
        }
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache"""
        try:
            cached_json = await self.redis.get(cache_key)
            if cached_json:
                return json.loads(cached_json)
            return None
        except Exception as e:
            self.logger.warning(f"Cache read error for key {cache_key}: {e}")
            return None
    
    async def _set_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Set data in Redis cache"""
        try:
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data, default=str)
            )
            self.logger.debug(f"Cached data for key {cache_key}")
        except Exception as e:
            self.logger.warning(f"Cache write error for key {cache_key}: {e}")
    
    async def _invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        try:
            keys = await self.redis.keys(f"{self.redis_key_prefix}{pattern}")
            if keys:
                deleted = await self.redis.delete(*keys)
                self.logger.info(f"Invalidated {deleted} cache entries matching {pattern}")
                return deleted
            return 0
        except Exception as e:
            self.logger.warning(f"Cache invalidation error for pattern {pattern}: {e}")
            return 0
    
    def _build_cache_key(self, query_type: str, params: Dict[str, Any]) -> str:
        """Build cache key from query type and parameters"""
        # Sort params for consistent cache keys
        sorted_params = sorted(params.items()) if params else []
        params_str = "_".join(f"{k}:{v}" for k, v in sorted_params)
        
        if params_str:
            return f"{self.redis_key_prefix}{query_type}:{params_str}"
        else:
            return f"{self.redis_key_prefix}{query_type}"
    
    async def _get_projection_data(self, projection_name: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get projection data for specific entity"""
        projection_key = f"{self.redis_key_prefix}projection:{projection_name}:{entity_id}"
        return await self._get_from_cache(projection_key)
    
    async def _list_projection_entities(self, projection_name: str, limit: int = 100) -> List[str]:
        """List entity IDs for a projection"""
        try:
            pattern = f"{self.redis_key_prefix}projection:{projection_name}:*"
            keys = await self.redis.keys(pattern)
            
            # Extract entity IDs from keys
            entity_ids = []
            prefix_len = len(f"{self.redis_key_prefix}projection:{projection_name}:")
            
            for key in keys[:limit]:
                entity_id = key[prefix_len:]
                entity_ids.append(entity_id)
            
            return entity_ids
            
        except Exception as e:
            self.logger.warning(f"Error listing projection entities: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get query handler statistics"""
        total_queries = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / total_queries if total_queries > 0 else 0
        
        return {
            'component': self.name,
            'type': 'QueryHandler',
            'queries_processed': self.queries_processed,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': cache_hit_rate
        }