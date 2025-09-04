from autocoder_cc.components.composed_base import ComposedComponent
from typing import Dict, Any, Optional
import asyncio
import logging
import httpx

class GeneratedSink_alert_sink(ComposedComponent):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.alert_type = config.get("alert_type", "email")
        self.logger = logging.getLogger(__name__)

    async def process_item(self, item: Any) -> Any:
        try:
            if self.alert_type == "email":
                await self.send_email_alert(item)
            else:
                self.logger.warning(f"Unsupported alert type: {self.alert_type}")
            return {"status": "success", "item": item}
        except Exception as e:
            self.logger.error(f"Error processing item: {e}")
            return {"status": "error", "message": str(e)}

    async def send_email_alert(self, item: Any) -> None:
        email_service_url = "https://api.emailservice.com/send"
        payload = {
            "to": "alerts@example.com",
            "subject": "Alert Notification",
            "body": f"Alert: {item}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(email_service_url, json=payload)
            response.raise_for_status()  # Raise an error for bad responses
            self.logger.info(f"Email alert sent successfully: {response.json()}")