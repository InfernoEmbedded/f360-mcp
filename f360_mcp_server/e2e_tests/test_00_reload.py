import pytest
import asyncio
from .conftest import SKIP_E2E
from .fusion_e2e import FusionE2E

@pytest.mark.skipif(SKIP_E2E, reason="F360_ADDIN_HOST not set")
@pytest.mark.anyio
async def test_scenario_00_reload(mcp_client):
    """Scenario 00: Update and Reload MCP Add-in."""
    f360 = FusionE2E(mcp_client)
    
    # 1. Check current version
    # Since get_version is background-safe, it should work even if the event bridge is broken
    version_res = await f360.call_tool("get_version")
    print(f"Current Add-in Version: {version_res}")
    
    # 2. Trigger update and reload
    # This will pull from master and restart both server and addin
    print("Triggering update_and_reload_mcp...")
    try:
        # This call might timeout or disconnect as the server restarts
        reload_res = await f360.call_tool("update_and_reload_mcp", {"branch": "master"})
        print(f"Reload result: {reload_res}")
    except Exception as e:
        print(f"Reload triggered (expected connection drop): {e}")

    # 3. Wait for restart
    print("Waiting 15s for components to restart...")
    await asyncio.sleep(15)
    
    # 4. Verify new version and connectivity
    # Re-initialize f360 as the session_id will change on restart
    # conftest handles the subprocess server restart if it crashes, 
    # but here we triggered a manual restart within the subprocess.
    # We might need to wait for the port to be available again.
    
    print("Verifying connectivity after reload...")
    for i in range(5):
        try:
            # We need a new client because the old one is bound to the old process/loop
            # but mcp_client fixture is function scoped, so it might be okay 
            # if we just retry the call.
            new_version = await f360.call_tool("get_version")
            print(f"Verified version after reload: {new_version}")
            assert new_version == "1.6"
            break
        except Exception as e:
            print(f"Retry {i+1} failed: {e}")
            await asyncio.sleep(5)
    else:
        pytest.fail("Failed to reconnect after reload")
