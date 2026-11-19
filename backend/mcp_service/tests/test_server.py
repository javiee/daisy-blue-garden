from django.test import TestCase


class AppModuleTest(TestCase):
    def test_mcp_route_exists(self):
        from mcp_service import app as app_module
        paths = [getattr(route, 'path', None) for route in app_module.app.routes]
        self.assertIn('/mcp', paths)

    def test_lan_host_is_allowed(self):
        # SDK transport security defaults to localhost-only: without this,
        # every LAN request is rejected with 421 Misdirected Request.
        from mcp_service import app as app_module
        self.assertIn('192.168.10.65:*', app_module.security.allowed_hosts)
