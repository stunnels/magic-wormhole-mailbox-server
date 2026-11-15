import os
from twisted.trial import unittest
from unittest import mock
from twisted.application.service import MultiService
from .. import server_tap

class Service(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch(
            "wormhole_mailbox_server.server_tap.load_or_create_replica_id",
            return_value="replica-1")
        patcher.start()
        self.addCleanup(patcher.stop)
        # Keep the ambient environment from influencing database selection.
        env_patcher = mock.patch.dict(os.environ)
        env_patcher.start()
        self.addCleanup(env_patcher.stop)
        for name in ("WORMHOLE_CHANNEL_DB", "WORMHOLE_USAGE_DB",
                     "WORMHOLE_ADDRID_DB"):
            os.environ.pop(name, None)

    def test_defaults(self):
        o = server_tap.Options()
        o.parseOptions([])
        cdb = object()
        udb = mock.Mock()
        aidb = object()
        r = mock.Mock()
        ws = object()
        with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_channel_db", return_value=cdb) as c_cdb:
            with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_usage_db", return_value=udb) as c_udb:
                with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_addrid_db", return_value=aidb) as c_aidb:
                    with mock.patch("wormhole_mailbox_server.server_tap.make_server", return_value=r) as ms:
                        with mock.patch("wormhole_mailbox_server.server_tap.make_web_server", return_value=ws) as mws:
                            s = server_tap.makeService(o)
        self.assertEqual(c_cdb.mock_calls, [mock.call("relay.sqlite")])
        self.assertEqual(c_udb.mock_calls, [])
        self.assertEqual(c_aidb.mock_calls, [])
        self.assertEqual(ms.mock_calls, [mock.call(cdb, allow_list=True,
                                                   advertise_version=None,
                                                   signal_error=None,
                                                   welcome_motd=None,
                                                   blur_usage=None,
                                                   usage_db=None,
                                                   addrid_db=None,
                                                   pubsub=None,
                                                   replica_id="replica-1",
                                                   )])
        self.assertEqual(mws.mock_calls, [mock.call(r, True, [])])
        self.assertIsInstance(s, MultiService)
        self.assertEqual(len(r.mock_calls), 3) # setServiceParent, check_addrid_generation, clear_connections

    def test_usagedb(self):
        o = server_tap.Options()
        o.parseOptions(["--usage-db=usage.sqlite"])
        cdb = object()
        udb = mock.Mock()
        r = mock.Mock()
        ws = object()
        with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_channel_db", return_value=cdb) as ccdb:
            with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_usage_db", return_value=udb) as ccub:
                with mock.patch("wormhole_mailbox_server.server_tap.make_server", return_value=r) as ms:
                    with mock.patch("wormhole_mailbox_server.server_tap.make_web_server", return_value=ws) as mws:
                        s = server_tap.makeService(o)
        self.assertEqual(ccdb.mock_calls, [mock.call("relay.sqlite")])
        self.assertEqual(ccub.mock_calls, [mock.call("usage.sqlite", "replica-1")])
        self.assertEqual(udb.register_replica.mock_calls, [mock.call()])
        self.assertEqual(ms.mock_calls, [mock.call(cdb, allow_list=True,
                                                   advertise_version=None,
                                                   signal_error=None,
                                                   welcome_motd=None,
                                                   blur_usage=None,
                                                   usage_db=udb,
                                                   addrid_db=None,
                                                   pubsub=None,
                                                   replica_id="replica-1",
                                                   )])
        self.assertEqual(mws.mock_calls, [mock.call(r, True, [])])
        self.assertIsInstance(s, MultiService)
        self.assertEqual(len(r.mock_calls), 3) # setServiceParent, check_addrid_generation, clear_connections

    def test_addriddb(self):
        o = server_tap.Options()
        o.parseOptions(["--addrid-db=addresses.sqlite"])
        cdb = object()
        udb = mock.Mock()
        aidb = object()
        r = mock.Mock()
        ws = object()
        with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_channel_db", return_value=cdb) as ccdb:
            with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_usage_db", return_value=udb) as ccub:
                with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_addrid_db", return_value=aidb) as c_aidb:
                    with mock.patch("wormhole_mailbox_server.server_tap.make_server", return_value=r) as ms:
                        with mock.patch("wormhole_mailbox_server.server_tap.make_web_server", return_value=ws) as mws:
                            s = server_tap.makeService(o)
        self.assertEqual(ccdb.mock_calls, [mock.call("relay.sqlite")])
        self.assertEqual(ccub.mock_calls, [])
        self.assertEqual(c_aidb.mock_calls, [mock.call("addresses.sqlite")])
        self.assertEqual(ms.mock_calls, [mock.call(cdb, allow_list=True,
                                                   advertise_version=None,
                                                   signal_error=None,
                                                   welcome_motd=None,
                                                   blur_usage=None,
                                                   usage_db=None,
                                                   addrid_db=aidb,
                                                   pubsub=None,
                                                   replica_id="replica-1",
                                                   )])
        self.assertEqual(mws.mock_calls, [mock.call(r, True, [])])
        self.assertIsInstance(s, MultiService)
        self.assertEqual(len(r.mock_calls), 3) # setServiceParent, check_addrid_generation, clear_connections

    def test_environment_databases_used_without_options(self):
        o = server_tap.Options()
        o.parseOptions([])
        cdb = object()
        udb = mock.Mock()
        aidb = object()
        r = mock.Mock()
        ws = object()
        env = {
            "WORMHOLE_CHANNEL_DB": "env-channel.sqlite",
            "WORMHOLE_USAGE_DB": "env-usage.sqlite",
            "WORMHOLE_ADDRID_DB": "env-addrid.sqlite",
        }
        with mock.patch.dict(os.environ, env):
            with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_channel_db", return_value=cdb) as ccdb:
                with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_usage_db", return_value=udb) as ccub:
                    with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_addrid_db", return_value=aidb) as c_aidb:
                        with mock.patch("wormhole_mailbox_server.server_tap.make_server", return_value=r):
                            with mock.patch("wormhole_mailbox_server.server_tap.make_web_server", return_value=ws):
                                server_tap.makeService(o)
        self.assertEqual(ccdb.mock_calls, [mock.call("env-channel.sqlite")])
        self.assertEqual(ccub.mock_calls,
                         [mock.call("env-usage.sqlite", "replica-1")])
        self.assertEqual(c_aidb.mock_calls, [mock.call("env-addrid.sqlite")])

    def test_options_override_environment_databases(self):
        o = server_tap.Options()
        o.parseOptions(["--channel-db=cli-channel.sqlite",
                        "--usage-db=cli-usage.sqlite",
                        "--addrid-db=cli-addrid.sqlite"])
        cdb = object()
        udb = mock.Mock()
        aidb = object()
        r = mock.Mock()
        ws = object()
        env = {
            "WORMHOLE_CHANNEL_DB": "env-channel.sqlite",
            "WORMHOLE_USAGE_DB": "env-usage.sqlite",
            "WORMHOLE_ADDRID_DB": "env-addrid.sqlite",
        }
        with mock.patch.dict(os.environ, env):
            with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_channel_db", return_value=cdb) as ccdb:
                with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_usage_db", return_value=udb) as ccub:
                    with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_addrid_db", return_value=aidb) as c_aidb:
                        with mock.patch("wormhole_mailbox_server.server_tap.make_server", return_value=r):
                            with mock.patch("wormhole_mailbox_server.server_tap.make_web_server", return_value=ws):
                                server_tap.makeService(o)
        self.assertEqual(ccdb.mock_calls, [mock.call("cli-channel.sqlite")])
        self.assertEqual(ccub.mock_calls,
                         [mock.call("cli-usage.sqlite", "replica-1")])
        self.assertEqual(c_aidb.mock_calls, [mock.call("cli-addrid.sqlite")])

    def test_channel_db_keyword_is_the_default(self):
        o = server_tap.Options()
        o.parseOptions([])
        cdb = object()
        r = mock.Mock()
        ws = object()
        with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_channel_db", return_value=cdb) as ccdb:
            with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_usage_db"):
                with mock.patch("wormhole_mailbox_server.server_tap.create_or_upgrade_addrid_db"):
                    with mock.patch("wormhole_mailbox_server.server_tap.make_server", return_value=r):
                        with mock.patch("wormhole_mailbox_server.server_tap.make_web_server", return_value=ws):
                            server_tap.makeService(o, channel_db="custom.sqlite")
        self.assertEqual(ccdb.mock_calls, [mock.call("custom.sqlite")])
