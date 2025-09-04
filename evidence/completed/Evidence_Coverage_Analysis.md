====================================================================================================== test session starts =======================================================================================================
platform linux -- Python 3.12.3, pytest-8.4.1, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/brian/projects/autocoder4_cc
configfile: pytest.ini
plugins: cov-6.2.1, xdist-3.8.0, anyio-4.9.0, timeout-2.4.0, asyncio-1.1.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 13 items

tests/regression/test_known_issues.py::TestCurrentLevel1State::test_generation_completes FAILED                                                                                                                            [  7%]
tests/regression/test_known_issues.py::TestCurrentLevel1State::test_files_created PASSED                                                                                                                                   [ 15%]
tests/regression/test_known_issues.py::TestCurrentFailures::test_imports_work XFAIL (Import paths broken - Level 3 failure)                                                                                                [ 23%]
tests/regression/test_known_issues.py::TestCurrentFailures::test_system_runs 