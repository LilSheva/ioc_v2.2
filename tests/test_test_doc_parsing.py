# -*- coding: utf-8 -*-
"""Полный тест-парсинга на тестовом наборе из папки .test_doc.
Этот файл сгенерирован автоматически на основе извлеченных и исправленных индикаторов.
Вы можете просмотреть этот файл глазами и отредактировать списки expected_*, если требуется.
"""
import os
import sys
import pytest

# Настройка путей импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import run_gui
from ioc_analyzer.core.config_manager import ConfigManager
from ioc_analyzer.core.service import AppService
from ioc_analyzer.adapters.document.docx_adapter import DocxAdapter
from ioc_analyzer.adapters.mail.exchange_adapter import ExchangeAdapter
from ioc_analyzer.adapters.export.local_fs_adapter import LocalFSAdapter
from ioc_analyzer.adapters.ip_block.mock_ip_block import MockIpBlockAdapter

class AppController(run_gui.GuiController):
    def __init__(self, settings_path: str):
        config_manager = ConfigManager(settings_path)
        config = config_manager.config_data
        
        doc_adapter = DocxAdapter()
        mail_adapter = ExchangeAdapter(
            email=config.get("ews_email", "dummy@test.com"),
            save_dir="."
        )
        export_adapter = LocalFSAdapter(
            share_path=config.get("network_share_path", "."),
            ioc_config=config.get("ioc_config", [])
        )
        ip_block_adapter = MockIpBlockAdapter()
        
        service = AppService(
            doc_reader=doc_adapter,
            mail_reader=mail_adapter,
            exporter=export_adapter,
            ip_block_client=ip_block_adapter,
            settings=config
        )
        super().__init__(service, config_manager)

TEST_DOC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.test_doc'))
SETTINGS_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))


def test_parse_folder_1_fstek():
    """Тест ФСТЭК набора в папке 1."""
    controller = AppController(SETTINGS_JSON)
    controller.set_mode("fstek")
    
    folder_path = os.path.join(TEST_DOC_ROOT, '1')
    docx_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.docx') and not f.startswith('~$')]
    controller.selected_files = docx_files
    
    success, ioc_data = controller.process_files()
    assert success is True
    
    # BDU
    expected_bdus = [('BDU:2026-07712', '240 93 6901.docx')]
    actual_bdus = sorted(list(set(controller.last_bdu_data)))
    assert actual_bdus == expected_bdus
    
    # IP
    expected_ips = ['109.172.85.63', '109.172.85.95', '141.105.65.160', '144.172.112.179', '165.231.141.126', '185.173.37.67', '185.209.30.41', '185.231.154.84', '185.231.155.111', '185.244.180.169', '185.91.127.92', '188.127.225.191', '188.127.227.226', '188.127.231.136', '188.127.251.146', '192.153.57.189', '192.165.32.78', '195.2.78.133', '195.2.81.99', '206.188.196.191', '37.120.247.173', '45.144.31.54', '45.67.230.39', '5.252.176.80', '62.113.114.209', '64.7.199.193', '77.232.39.47', '77.232.42.107', '78.128.112.209', '82.202.173.167', '87.251.66.206', '89.23.113.204', '91.210.107.135', '91.219.148.93', '94.131.121.10', '94.198.52.200', '94.198.52.210', '96.9.124.207']
    actual_ips = sorted(list(set([clean for _, clean, _ in ioc_data.get('IP', [])])))
    assert actual_ips == expected_ips
    
    # DNS
    expected_dns = ['astro-kluch.ru', 'ccdertsfrp1.wris.monster', 'cckitsfrp1.n3x1lo.pro', 'cddcvesfhfp1.wris.monster', 'cdn.electropriborzavod.ru', 'chronback49in.duckdns.org', 'cloud.electropriborzavod.ru', 'cnhgenfhfp2.wris.monster', 'cumfpo90sing.agddns.net', 'deefveskiip2.wris.monster', 'disk.npo-iskra.ru', 'dnqhj7.top', 'docs.npo-iskra.ru', 'electropriborzavod.ru', 'f.npo-iskra.ru', 'files.npo-iskra.ru', 'fira24sonstablee.agddns.net', 'laipros50.agddns.net', 'myrostelecom.ru', 'npo-iskra.ru', 'op2a.beemooshka-v1.art', 'procdia42ecte.agddns.net', 'qdkitsorp2.n3x1lo.pro', 'qdprtsorp2.wris.monster', 'qxpngendvvp1.wris.monster', 'rhel.opsecurity1.art', 'sec.opsecurity1.art', 'static.myrostelecom.ru', 'test.npo-iskra.ru', 'urbantvpn.online', 'viedeu98.agddns.net', 'wholewell.online', 'www.astro-kluch.ru', 'www.cloudaro.help', 'www.dnqhj7.top', 'www.genesisweb-test.fr', 'www.n8nsantos.top', 'www.pasdaran06.com', 'www.sovra.site', 'www.storeclosures.com']
    actual_dns = sorted(list(set([clean for _, clean, _ in ioc_data.get('DNS', [])])))
    assert actual_dns == expected_dns
    
    # URI
    expected_uris = ['http://172.86.75.102/', 'http://193.149.129.113/', 'http://195.2.79.245/service.exe', 'http://195.2.79.245/winload.exe', 'http://195.2.79.245/winload.rar', 'http://195.2.79.245/winsrv.rar', 'http://195.2.79.245/winupdate.exe', 'http://62.113.115.89/offel.exe', 'http://82.115.223.218/', 'http://82.115.223.78/private/msview.exe', 'http://82.115.223.78/private/spoolsvc.exe', 'http://82.115.223.78/private/svchost.exe', 'http://82.115.223.78/private/sysmgmt.exe', 'http://85.209.128.171:8000/AkelPad.rar', 'http://88.214.25.249:443/netexit.rar', 'http://89.110.95.151/dwm.exe', 'http://89.110.98.234/Rar.exe', 'http://89.110.98.234/code.exe', 'http://89.110.98.234/rever.rar', 'http://89.110.98.234/winload.exe', 'http://www.astro-kluch.ru/u9a4', 'http://www.cloudaro.help/g588', 'http://www.dnqhj7.top/yy41', 'http://www.genesisweb-test.fr/mj0zmj0zmj0zmj0zmj0zmj0zmj0zmj0zmj0zmj0z', 'http://www.n8nsantos.top/ksb6', 'http://www.pasdaran06.com/khc6', 'http://www.sovra.site/wzrd', 'http://www.storeclosures.com/hxo1', 'https://api.telegram.org/bot7157076145:AAG79qKudRCPu28blyitJZptX_4z_LlxOS0/', 'https://api.telegram.org/bot7562800307:AAHVB7Ctr-K52J-egBlEdVoRHvJcYr-0nLQ/', 'https://api.telegram.org/bot7804558453:AAFR2OjF7ktvyfygleIneu_8WDaaSkduV7k/', 'https://api.telegram.org/bot7864956192:AAEjExTWgNAMEmGBI2EsSs46AhO7Bw8STcY/', 'https://api.telegram.org/bot8039791391:AAHcE2qYmeRZ5P29G6mFAylVJl8qH_ZVBh8/', 'https://api.telegram.org/bot8044543455:AAG3Pt4fvf6tJj4Umz2TzJTtTZD7ZUArT8E/', 'https://cdn.electropriborzavod.ru/index', 'https://cloud.electropriborzavod.ru/files/d8287185e4ae695a', 'https://discord.com/api/webhooks/1357597727164338349/ikaFqukFoCcbdfQIYXE91j-dGB-8YsTNeSrXnAclYx39Hjf2cIPQalTlAxP9-2791UCZ', 'https://discord.com/api/webhooks/1369277038321467503/KqfsoVzebWNNGqFXePMxqi0pta2445WZxYNsY9EsYv1u_iyXAfYL3GGG76bCKy3-a75', 'https://discord.com/api/webhooks/1370623818858762291/p1DC3l8XyGviRFAR50de6tKYP0CCr1hTAes9B9ljbd-J-dY7bddi31BCV90niZ3bxIMu', 'https://discord.com/api/webhooks/1386588127791157298/FSOtFTIJaNRT01RVXk5fFsU_sjp_8E0k2QK3t5BUcAcMFR_SHMOEYyLhFUvkY3ndk8-w', 'https://discord.com/api/webhooks/1388018607283376231/YYJe-lnt4HyvasKlhoOJECh9yjOtbllL_nalKBMUKUB3xsk7Mj74cU5IfBDYBYX-E78G', 'https://discord.com/api/webhooks/1396726652565848135/OFds8Do2qH-C_V0ckaF1AJJAqQJuKq-YZVrO1t7cWuvAp7LNfqI7piZlyCcS1qvwpXTZ', 'https://discordapp.com/api/webhooks/1355019191127904457/xCYi5fx_Y2-ddUE0CdHfiKmgrAC-Cp9oi-Qo3aFG318P5i-GNRfMZiNFOxFrQkZJNJsR', 'https://discordapp.com/api/webhooks/1363764458815623370/IMErckdJLreUbvxcUA8c8SCfhmnsnivtwYSf7nDJF-bWZcFcSE2VhXdlSgVbheSzhGYE', 'https://discordapp.com/api/webhooks/1392383639450423359/TmFw-WY-u3D3HihXqVOOinL73OKqXvi69IBNh_rr15STd3FtffSP2BjAH59ZviWKWJRX', 'https://disk.npo-iskra.ru/files/1a427fba.zip', 'https://docs.npo-iskra.ru/data', 'https://f.npo-iskra.ru/m2.png', 'https://files.npo-iskra.ru/direct/7b44646d-1b09-45b1-8977-62327e6ec1e7/1a427fba/%D0%98%D1%81%D1%85%D0%BE%D0%B4%D1%8F%D1%89%D0%B5%D0%B5%20%E2%84%96%207784%20%D0%BE%D1%82%2010.10.2025%20%D0%BE%D1%82%20%D0%90%D0%9E%20_%D0%9D%D0%9F%D0%9F%20_%D0%97%D0%B0%D0%B2%D0%BE%D0%B4%20%D0%98%D1%81%D0%BA%D1%80%D0%B0_.zip', 'https://static.myrostelecom.ru/provider', 'https://y.txpx.tech/47d605e9aaee4f6b8775a58454a7d04b/47d605e9aaee4f6b87']
    actual_uris = sorted(list(set([clean for _, clean, _ in ioc_data.get('URI', [])])))
    assert actual_uris == expected_uris
    
    # Email
    expected_emails = ['info@fsb.msk.su']
    actual_emails = sorted(list(set([clean for _, clean, _ in ioc_data.get('Email', [])])))
    assert actual_emails == expected_emails
    
    # SHA256
    expected_sha256 = ['0002afc2839af82725499ed50f75a193b01a32111253ba3d8647189d8f0f2c28', '0e91d50da1d39d505b3bbec3c759d1fde6e51373c10900b68a45849b073d2684', '0eafb9dbaf9f72e61ee65926a61b3b07a3a5d1ab1a47b0bb6e3e8bc3c9f9f9f2', '0f37d45c70d5fae0c76b9eeed454b4a0ef58609ce99534d1ca9365fac5155fc9', '0f59de6d6b1a60079a99cff403c2a3683de15c7edaff79ba2cb1d4dae43c7b41', '0f728de0881dc37e79d3e065a331b21f6acadb7d129db2a5bfc27551bba3892e', '13299152ead4b1592843b9eddfbfd7b320a5fdec09c568a11ec7f9834cd7a610', '13c9c6cc9b7a180949e29baa38efde81e06e7e0a29be3b4ed98eb10af4ab60ef', '1444b49c6e6183f856a4f18ea6a657ae3033b47a45c1152dcf60dc361a7826d7', '17d9359625b47fcf65ccdb59bd0dba6c44f8e140d8eedc37a8923baa8aefd481', '1cc3edb1758fcadd97cd835f6b516db3aa8c3cbc563776080ab8ebf378536c71', '1ecad44696fcc6631796a79424b2410e8c61c957d8e54106bdb78c7dd9986cde', '21eba25e3090d8ad943fd5371da3e6598c486b67571f0b75fc910c6aec8edde1', '249537c07990f0b829ed94ae4b64585a38f9c7b08fa1f5f530489625521f7742', '28dbae86db73868758301c140f2b2c7bc19ce3862e0cd21966bfe9d3e7476e4a', '29194e0d1464211b92cef881c6b5decd6cc353fb791715448bc1d2705e711edb', '2a98af0a0eb9eb4db2bae7d6cec21b94630eadd2ad66d41d1d9dad76b6f0db60', '2cde77279abfdb1472f21d393383c5442d4e661d481b192cb5c98d218998d810', '2d7328d0623b36c31e22b1b12ece8094aa232ccdb7ea92ec860ff6b7030fbe93', '2e4d8d5573c36aff89bb773b97ca6d6a11c85ad436ee13baba507517e9e8658d', '2eff8367be0facf74b74384f3b45e83cd327510c64a216355e8f6e8948634033', '30a555a0aad7d370fac2f812a062f6bbbec671c46c1457a759e25945d3539b94', '30b26707d5fb407ef39ebee37ded7edeea2890fb5ec1ebfa09a3b3edfc80db1f', '36d9db678b6895cd08e8673438b3de44a2cd589329c68cbf214067a38cd47d0e', '37a5bd6361e48586749594f5fb853c4b79a0931f979f03bdb31dc91c526924ec', '3ee7ae78964f35ec56a1d5d6026482e40e6ca9a59f9f474fff475e32231e2ff4', '46a4f04b3a88d2ecfc98c3488c5efe485eb0e48d4b1701123319dec2ceea96fc', '49d4cd2bf3b65db2ecbaaa46944b2b76786de51724fc73c44d0d8e485fa1f3b5', '5169a14a85833911e25934854f74f644926a1498cdc4ee9f2aeaf167c7995f8b', '51a6635806d1b4bf7e523df29fc4b74d5a7a5bc721a347e90b4586fa20dbf87f', '51f0806e39ca2fd866ebad11866affb3299b291319a271eb7c71baa3458a1dbd', '551c0455a608edd88ecd6946c93ed2ac9a68a48148630975a17905205629f617', '5535ec963580b36561293c9bff918dee4c6c8438abd7a76a31925f4245bcd65c', '57d42999aa0010a0c2c96076ff5097bf48bd487949733a15242bdd58d2f3553b', '57d55b21366fda8546d16ec7beeac43f3f2ffec05eca891082fb059348598765', '58cb73a09b0cb497119bf6450f20d8343f01ea8c8ace72cc71e9414920f77342', '5cef48c73704040bea45f85601cbc0fe40b5dea84721344b1cfd67c62650e996', '5f157979c0a4b58c385dda780f584269d3e174b6816a9e7483504f04818beeb4', '5f1d3992e426f47b572af12160f3cc7ac6c90634b17fd6a087eb1644a60a71f8', '6491be745661f1d1f01eaf9d5c4f15dbc494c81ca11d2ea04aeddf7b8b0d0314', '650bd3fec6160759878f58962d2cffe9cf0074b59b01e569621335470da1e005', '65e35f68c12938f133fb120565f3c8221c53d3b841dbddb98e0d3c6054f2c7be', '67751c565593ad4557e73a521b2da96431937296f9dba7d03839e9496031fcbb', '6ae3d948ce0c0eebc17fe53a023598d4d663e1cb967c9c012070fd86a2ce078f', '6bcf8a73a83068626306065789df6efbbb81abb8b66c6e75d06c75c871ecbdfc', '6ccd834fdbba07cf071e3c6de703fbc7f9de10584df127ced27537db2e1a5a03', '6d745834032d55e804e2a423529d9f663254ea07185eb96f2f5f089941668b7c', '77b9a372ee97c0c832a618def71940e65a3c3d1eca1f8cb34ff395fd39cd23a2', '79490132a67eaeaf1e5242f3dcecced7f4b9983557b2f145a83227c9a89a92e7', '7b1da4c6c9b44444e9a6c4d58f7676af52ecd504fe2657fce9ce1adc2b711055', '7e0146e5e8798d7c647312fd5b0d4cc1a0381a367f41b6ba589381db7c80eafb', '7fbb29f8724fddfb32b29543e046cf4aceab8f10e5120150f58d7a119162c631', '809e41c3a700ccaaaf2602b62e162a4ae59315ef86ee37daca8c7064d01bf086', '82581c8043ac12ef3e5c35572759fb494775aff210b060ebd7492d3134b25024', '87290ce0d3bd3a680d092fe038a9e80b37b3358502d511236ec5df50e4bfe6ee', '873c4fbf47b8036238b52fd02bf7846d86df4c87f6dbf302db9a959371d464ff', '87b34520d791933733b8f9f27088a68d9b4e67b2db869be50de2a6e01a92077f', '8b43430136fcc9ef43f201febddbdd608cfebd25c611c13a146a66883b0f201e', '8ce769d07989f59ece5f137afce84e4075fcc1010426bf1a77378d7e2a628995', '8d3a411ea9225d8bc0503235e0832025e7a3260b9bcdb85119ccb508c4547107', '8ea0bd323618e47c2f002d1f0e85d07eb7440ff7efa9e91329f49819b46438f2', '8fc01417832dd08559609ef0667149a24897380113294e10b44694071afd22f2', '93305e688c22d1b39f8ec6fc86fe01482bc6cab896ceea7965da4448a75a2a9a', '9959a16f1fd19191de2d40cad5dbf4e63c62eb55487068de0a6f6b4696bccd72', '9a0d5e90444d94778775180b6373a6d4f0ca293764f51b4371f4ab5452f202e3', '9f5a79d9c5100de0af25bec6f640264e4db367d1a6cd1804e1e2a1772637c30a', '9fadd4c62a79e97cc0c65c8bf25bce2721d0ca7dfac9dc6aaeb47df5c8f4508e', 'a381ab82d519159cb17e897f3d2a9ce9a122ff5941f734a14df89a7b2f0667da', 'a9e316ba471b1bf606ee3c77ae8bf4b6552e139928d6071b7dca3f847c571c92', 'ad61f0cd17915e099c5c8728aad8443b85284a82566648ddcaeb08436878f3a9', 'ad79af28fb9a5086dde3c071c32ff1fe9eae934c6edd1da88776fe6d41c201e1', 'b10dc9ba6089e372ab63d4ec30f31654abccfed0ade0c8aa0eac1724cc4c6d17', 'b44b43f7ecdacaa56ca9fc8a6cc8804218ff511961ca9143b612b2dea652cf99', 'bcc0cda02a11acbd0923db43099f854038caaf03ddbf59e1d53452641119d42a', 'be317297dae16dd7b90ddd972b40aca810ff52f6a01a06c96d2dc4bbdd08231d', 'be44c606c2114534222f1be794a37a7d113d849376328149d60d6b67c1318946', 'c0de8f8292721192cabe33ac51f2b26468bb2ca70f1e49cfb4647ff70bb14d23', 'c1949fe4bdf693ae4e62f52bc728bf3b455b47862298fdfcd61fefa7e304d7cf', 'cad9677ad4198b1710d390747e98b6b5e29ceab18f16e8ab12be5b6b8aab4021', 'd291f0bfa4a82cad1c95d11ebabb1539b9d9d5837534a8bd5b659462dd2eeabd', 'd3c25ee081761c600669597c6ad4effd02f2a5d1171af267b04b572698554d2e', 'd47590e49f0418396b75dbacf5bb64735da951af408b0562d87234e8d0a63651', 'd597eee02fc30b3bc1c523e8afad63f75912c4c2a47d3e981c5950a00bd76a6d', 'd65c998e8b5746c98a8e4eefeb2de3dd50ce69b84fc94c9353bc06b7cb278192', 'd6763d0d0c2b12ea9124ccaea3e6497bfc2cb4a3a9dfe6239a734afeaf372013', 'd984d1de0c18d0290450b990b572a7e8454b095295810bdea6ced9151973a350', 'da0f242578f67b101761b8e0bb4136ee757092f0bebb32c78706572591f521da', 'dd7b95d9e2a8317d3f7f6480b30677d95aa5398ee4dab56e55b34f1c36bad5f3', 'df9b0d259a869c2bf71cbcdd90643750ffad067acdf8480e2981531f47ebf930', 'e19ed0b50872d467ac313175c955382fd9bca437ad5932856a690823455049fd', 'e45a1fca84ea0de58f88fe8930b0309f9d736b7384a12f01b7843a9f6469d64b', 'e49eb564c061b132c411859e79e8026f46059f4be759d812e2043956400d32ad', 'e6582e5a4c62f461661cc0687be45a5bb68c2081d6d8c5d3598d53770962f453', 'e76fe4cbd4d0ec8d78bc05b03f6c159f36fd6cac26c3002373bf380b069949d8', 'e7aa94e76acf181b4fd6fbfdcf599ce677c5f95675b50e68fe2d43ea72202bf7', 'e7e52e15636cb32ac227f4833adf75a0bacca3d8b9081f3e3bdcb8243a8b68aa', 'e890107ebb7086f992d41fa739a572644a98edf1da6421fa76abb78b721d4059', 'e90f7f8594333e0a955a1daccbf5e9030ea86fa3c5c39f58b69d313304020fdd', 'e9b89ae1cf3c7263cfcd4c56ce826565fa619b1a5f867d2a139f84d19bc921a3', 'ec2fc991758ae4b28c1691a00470c3723171db69f901627c8e07b7f8dce221ca', 'ee33385b20be0d457f4acccc5d222eb11adb7683c96b4dfd30d2772361f2346b', 'ef8305ea0a53676a04da70abb9d18ea36acba67404e5bfdeddc201d95ec1c22a', 'f0cc251a2eb4a73aa20a8a90223600c9053a12ee94a1698ccbb9d189758ff4cb', 'f12a073a88b076875dbd4ea36f02e803a8ef10c9d8892b5557d8fb46d2c68016', 'f5635d9afd0116846cf447e218c561cc111c50e6a994b5c719556ce28c4e64d6', 'f71873f37fbd5a5870a51db75d8b99ff83ac2d03f0e5682e943d8cb9c84b6129', 'f73fe375cddea8a869edad7dd33b3783090113ff0dd0ab3b4e275006be40cadc', 'f80240fd14abe8d62cb2fae7a8afce34f07337d375eaccc5d9cb118f461377a4', 'f9b0aad1cff4540ecc0c0ae39d5c7362032116d7c6be86d89dfe39130ef55f95', 'fa47c264f7fbecfbe00078a68056d8bbcca80dd6f57e0551063bf387424fb4dd', 'fb0d79602dfac97f5e36f5f0287d167271d04294dccfdccfa15a88ff6dba11b7', 'fb1811eaa27caeb84077900e5cfe7000bc1130a4dc51d3a2f93340080e16776f', 'fb1c815365622a37328570c4b3703654fe7e5c9e9eae335542bac6090e2f9a2e', 'fcd63239e4065414ba23d1546e18248653f6d937276520f16cf9a29308f65439', 'feb8ea7374a79c67252f675a5f88113d4a6cf4762cf5d7c4fd5ff3653622927b', 'fecb289bf6acc31c00f2c73ef269bfda4325f45803592d37256dda289dc4d9aa']
    actual_sha256 = sorted(list(set([clean for _, clean, _ in ioc_data.get('SHA256', [])])))
    assert actual_sha256 == expected_sha256
    
    # MD5
    expected_md5 = ['078BE0065D0277935CDCF7E3E9DB4679', '087743415E1F6CC961E9D2BB6DFD6D51', '091FBACD889FA390DC76BB24C2013B59', '0E6578DC4F95565C1426E3F188D36460', '0EFEB6B9699B7FBEBF5E0657A14C7F88', '0F955D7844E146F2BD756C9CA8711263', '1083B668459BEACBC097B3D4A103623F', '1241455DA8AADC1D828F89476F7183B7', '2D85FB64F37E78913C20EE9C886D33BE', '2ED5EBC15B377C5A03F75E07DC5F1E08', '2FBA6F91ADA8D05199AD94AFFD5E5A18', '32F9C7FB69BB7EE76E19F4BBEE16F4B3', '33ED1534BBC8BD51E7E2CF01CADC9646', '42E165AB4C3495FADE8220F4E6F5F696', '4EDC02724A72AFC3CF78710542DB1E6E', '5470DD5E57D0060D98891D8F5740E5B2', '6FE8943F364F6308C2E46910BFFEFEAF', '71612EBCC591B2475D3488E5580DB56A', '83267C4E942C7B86154ACD3C58EAF26C', '8B66D1EDA2F1E0A858E0747307552E0B', '925EEA2692C4D8DEC9B8F1C94A8C8229', '9A9B1BA210AC2EBFE190D1C63EC707FA', 'B8FE3A0AD6B64F370DB2EA1E743C84BB', 'BDC4FD7329E5F5BAA7964B24C61171FD', 'C0F81B33A80E5E4E96E503DBC401CBEE', 'C73C545C32E5D1F72B74AB0087AE1720', 'C75665E77FFB3692C2400C3C8DD8276B', 'CD46316AEBC41E36790686F1EC1C39F0', 'D528158A6459A71A33E3C05A606B6B33', 'DF95695A3A93895C1E87A76B4A8A9812', 'E5B2E603861E8E01B7A03122280F2E90', 'EEDA5A1A503233F6DE3EAC3F34CABC2F', 'F1DCA0C280E86C39873D8B6AF40F7588', 'F812BDAECDCEC818D015B1A8D1D21C40']
    actual_md5 = sorted(list(set([clean for _, clean, _ in ioc_data.get('MD5', [])])))
    assert actual_md5 == expected_md5

    # File
    expected_files = [
        "1.zip",
        "Aкт cвepки взaимopacчeтoв пpeдпpиятия № 372 oт 24 нoябpя 2025 гoдa.exe",
        "Scan_САО ВСК_Претензионное письмо_278 [множество пробелов].exe",
        "Аппарат Правительства Российской Федерации по вопросу отнесения реализуемых на территории Сибирского федерального округа [множество пробелов].rar",
        "Бланк.doc",
        "Декабрьский заказ.rar",
        "Декабрьский заказ.vbe",
        "Исходящее № 7784 от 10.10.2025 от АО _НПП _Завод Искра_.pdf.lnk",
        "Исходящее № 7784 от 10.10.2025 от АО _НПП _Завод Искра_.zip",
        "Коммерческое предложение №481 от 02.12.2025.cmd",
        "Коммерческое предложение №481 от 02.12.2025.rar",
        "Предложение коммерческое Орион №217 от 02.12.2025.rar",
        "Предложение коммерческое Орион №217 от 02.12.2025.scr",
        "Результаты медицинского обследования [множество пробелов].exe",
        "САО ВСК_Претензионное письмо.rar"
    ]
    actual_files = sorted(list(set([clean for _, clean, _ in ioc_data.get('File', [])])))
    assert actual_files == expected_files


def test_parse_folder_2_gossopka():
    """Тест ГосСОПКА набора в папке 2."""
    controller = AppController(SETTINGS_JSON)
    controller.set_mode("gossopka")
    
    folder_path = os.path.join(TEST_DOC_ROOT, '2')
    docx_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.docx') and not f.startswith('~$')]
    controller.selected_files = docx_files
    
    success, ioc_data = controller.process_files()
    assert success is True
    
    # Разблокировка IP
    expected_unblocks = ['142.250.64.110']
    actual_unblocks = []
    if controller.last_unblock_data:
        actual_unblocks = sorted(list(set([clean for _, clean, _ in controller.last_unblock_data.get('IP', [])])))
    assert actual_unblocks == expected_unblocks
    
    # IP
    expected_ips = ['100.51.239.164', '101.99.91.150', '102.98.80.61', '103.194.107.168', '103.43.18.10', '103.77.246.199', '111.48.234.110', '111.92.243.40', '116.198.41.59', '116.204.171.70', '118.68.217.64', '124.156.165.214', '129.226.167.253', '130.12.181.93', '130.12.181.94', '136.0.157.158', '138.226.236.84', '138.226.237.155', '138.226.237.166', '138.226.237.188', '138.226.237.194', '138.226.237.196', '143.92.61.65', '144.202.43.95', '147.124.219.209', '148.113.5.4', '148.178.119.85', '148.178.39.57', '148.178.43.87', '148.178.44.227', '148.178.45.72', '148.178.51.207', '148.178.52.57', '148.178.60.57', '148.178.65.94', '148.178.70.49', '148.178.71.71', '148.178.77.76', '148.178.80.206', '148.178.83.49', '148.178.84.112', '148.178.85.246', '148.178.87.48', '148.178.89.46', '148.178.91.186', '155.94.172.177', '158.94.208.6', '160.202.133.194', '162.252.199.45', '162.254.24.185', '162.62.231.174', '163.181.77.215', '166.117.47.92', '172.245.4.221', '173.255.203.221', '176.65.132.175', '178.16.55.39', '178.212.12.41', '18.190.71.162', '18.191.154.93', '18.212.247.86', '185.11.61.223', '185.117.0.85', '185.214.74.27', '185.222.58.40', '185.230.88.13', '185.76.242.166', '192.119.166.13', '192.210.186.231', '192.227.152.84', '193.24.123.232', '194.68.225.38', '194.87.37.59', '195.24.237.39', '2.59.135.83', '20.2.140.201', '207.148.122.138', '207.56.13.76', '207.56.192.203', '207.56.195.76', '207.56.197.120', '207.56.201.58', '207.56.203.74', '208.64.33.69', '213.155.29.81', '223.26.62.209', '23.83.209.27', '3.209.181.254', '3.86.33.166', '34.230.242.7', '35.83.162.55', '37.143.76.103', '37.143.76.118', '37.27.200.165', '37.27.21.37', '38.148.203.82', '45.151.91.164', '45.153.34.109', '45.156.87.208', '45.82.160.48', '45.84.138.50', '45.95.232.51', '46.151.182.4', '46.224.191.117', '46.62.245.12', '47.83.230.53', '47.93.141.98', '48.217.50.253', '50.17.86.250', '51.15.124.236', '52.21.176.23', '52.5.18.208', '59.184.124.51', '62.3.58.68', '65.87.7.251', '69.165.67.85', '77.105.161.26', '77.42.19.39', '77.42.29.135', '77.42.82.203', '8.218.178.70', '81.163.30.15', '82.23.183.41', '83.217.209.11', '85.17.40.98', '91.132.93.251', '91.189.117.8', '91.214.78.60', '91.92.240.211', '91.92.240.29', '92.119.125.184', '95.140.148.226', '95.211.45.184', '95.216.177.223', '95.217.25.219', '95.217.27.33', '95.217.27.8', '95.81.123.133', '96.9.124.110', '99.83.220.247']
    actual_ips = sorted(list(set([clean for _, clean, _ in ioc_data.get('IP', [])])))
    assert actual_ips == expected_ips
    
    # DNS
    expected_dns = ['24-kg.com', '789club1.se.net', 'accutane18.us.org', 'adoption.sa.com', 'animalrecord.xyz', 'arasida.sa.com', 'artemkalenadov-42277.portmap.host', 'backend-knwv.onrender.com', 'basvurudanis.sbs', 'beeftexture.xyz', 'beittikvah.us.com', 'bitrix24.slg-sauna.ru', 'bryw.cn.com', 'crrhelp.top', 'distancebedroom.xyz', 'dpn.uk.net', 'dup.erom-e.com', 'dup.zeronoiseclassroom.com', 'e-konutbasvuru.sbs', 'eastwell.uk.com', 'emg.uk.com', 'evekonutabasvur.cfd', 'fbnmoon.coupons', 'fbnmoon.fun', 'fbnmoon.space', 'fbnmoon.top', 'fbnmoon.world', 'fbnmoon.xyz', 'feq.uk.com', 'food-family.icu', 'fuzzy-pickle.cc', 'gamers.uk.net', 'gbr.erom-e.com', 'gbr.zeronoiseclassroom.com', 'gonebornes.com', 'goo.erom-e.com', 'goo.zeronoiseclassroom.com', 'gordonsmitharchitect.co.uk', 'hhv.uk.com', 'hitclub.ru.com', 'hitclub33.eu.com', 'hostikslu.is', 'importhd.cyou', 'indian-lotus.cc', 'inforash.com', 'irregukw.cyou', 'kurasizhemenkatil.cfd', 'kurasizkatilim.sbs', 'leb.erom-e.com', 'leb.zeronoiseclassroom.com', 'leprixnet.com', 'matalan.uk.com', 'mirelvse.cyou', 'nightcopper.info', 'ollertonandboughton.uk.com', 'oui.erom-e.com', 'oui.zeronoiseclassroom.com', 'paxenro.paxenro.shop', 'peacockes.ie', 'portwinejoke.icu', 'readconfig.x1s.icu', 'reveiley.cyou', 'rumordoz.cyou', 'schemaqa.cyou', 'securityfenceandwelding.com', 'solfson.com', 'springdesignpartners.us.com', 'sps-163.ru', 'sub.erom-e.com', 'sub.zeronoiseclassroom.com', 'swimglii.cyou', 'telecom-connect.online', 'toki.e-konutbasvuruekran.sbs', 'toki.evekonutabasvur.cfd', 'toki.konutbasvuruturkiye.sbs', 'toki.sosyalkonut.cfd', 'toki.vatandasbasvuru.cfd', 'tokl.basvurusondonem.cfd', 'topshop.in.net', 'triniliu.cyou', 'trustbeam.space', 'uberdeltagss.com', 'visa.br.com', 'wvw.erom-e.com', 'wvw.zeronoiseclassroom.com', 'www.hubion.site', 'www.mariseaverguyglobal.com', 'www.mariseaverguyglobalbackup1.com', 'www.mariseaverguyglobalbackup2.com', 'www.www-161bet.com', 'yepork.com', 'yffsoksss888.com']
    actual_dns = sorted(list(set([clean for _, clean, _ in ioc_data.get('DNS', [])])))
    assert actual_dns == expected_dns
    
    # URI
    expected_uris = ['http://130.12.180.20:36695/c.sh', 'http://138.226.237.196', 'http://144.31.221.103/a', 'http://144.31.221.132/a', 'http://158.94.208.6/h8jfdmdWS/Login.php', 'http://158.94.208.6/h8jfdmdWS/index.php', 'http://5.8.18.106/ce369e7324834845.php', 'http://62.60.226.159/Setup.exe', 'http://65.87.7.251', 'http://98.142.251.115/cache', 'http://zapsnn.com', 'https://138.226.236.84/', 'https://138.226.237.155/', 'https://138.226.237.166/', 'https://138.226.237.188/', 'https://138.226.237.194/', 'https://37.27.200.165/', 'https://37.27.21.37/', 'https://46.224.191.117/', 'https://46.62.245.12/', 'https://77.105.161.26/', 'https://77.42.19.39/', 'https://77.42.29.135/', 'https://77.42.82.203/', 'https://95.216.177.223/', 'https://95.217.25.219/', 'https://95.217.27.33/', 'https://95.217.27.8/', 'https://98.142.251.115/caching', 'https://animixplay.com.co/', 'https://brodownload9s.com/code/meztombsha5ha3ddf4ytanbygm', 'https://cdn.coddejs.online/js/smart.php', 'https://cdn.jsdelivr.net/gh/az2-prd-rs01/s3-backet-cloud73-s1/gfn-srvc', 'https://cdn.jsdelivr.net/gh/browse-fb-clock/legendary-value/files', 'https://cdn.jsdelivr.net/gh/browse-fb-clock/octo-carnival/filen', 'https://cdn.jsdelivr.net/gh/browse-fb-clock/urban-lamp-class/pull', 'https://cdn.jsdelivr.net/gh/browse-via-api/api-key-sash/logs', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/2b-rvy-6o-fv-ho/dreamt-undrafted', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/475event-bu7s-sync74-prx5-eu2/splicing', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/fexw8qvyvqj8qe-identity-token-issuer/oiaaai', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/fexw8qvyvqj8qe-identity-token-issuer/outh', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/fexw8qvyvqj8qe-identity-token-issuer/set1', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/fexw8qvyvqj8qe-identity-token-issuer/trc20', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/identity-broker454-cloud6546/dexvphujrsh', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/identity-broker454-cloud6546/graftingawkward', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/n-state-manager-cache128/jpg', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/n-state-manager-cache128/load', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/n-state-manager-cache128/sdvvv12', 'https://cdn.jsdelivr.net/gh/service28-discovery-registr/n4-g567-d8-af7/csvc', 'https://dup.erom-e.com/', 'https://dup.zeronoiseclassroom.com/', 'https://food-family.icu/api/send', 'https://gbr.erom-e.com/', 'https://gbr.zeronoiseclassroom.com/', 'https://goo.erom-e.com/', 'https://goo.zeronoiseclassroom.com/', 'https://inforash.com/auth/logout-controller.js', 'https://inforash.com/auth/logout-service.js', 'https://inforash.com/auth/profile-module.php', 'https://jawks.t3.storage.dev/Verify-me-to-continue-ID-75099.html', 'https://jswidget.all-widget.com/latest//locales/ru/common.json?v=6.0.0', 'https://leb.erom-e.com/', 'https://leb.zeronoiseclassroom.com/', 'https://leprixnet.com/3s5f.js', 'https://leprixnet.com/js.php', 'https://miotech.be/', 'https://mirelvse.cyou/api', 'https://official-jaxxwallet.com/host.exe', 'https://oui.erom-e.com/', 'https://oui.zeronoiseclassroom.com/', 'https://portwinejoke.icu/menu.js', 'https://premiumdiagnostics.pk/', 'https://solfson.com/1d1d.js', 'https://solfson.com/js.php', 'https://steamcommunity.com/profiles/76561198748625465', 'https://sub.erom-e.com/', 'https://sub.zeronoiseclassroom.com/', 'https://swissnoli.eu/', 'https://telegram.me/v11kng', 'https://tibetosi.com/cache', 'https://wvw.erom-e.com/', 'https://wvw.zeronoiseclassroom.com/', 'https://yepork.com/auth/logout-controller.js', 'https://yepork.com/auth/profile-module.php']
    actual_uris = sorted(list(set([clean for _, clean, _ in ioc_data.get('URI', [])])))
    assert actual_uris == expected_uris
    
    # Email
    expected_emails = ['cristian.iancu@rakocziujfalu.hu', 'dana@mamaespot.com', 'email@promkomitet.space', 'infos@krysegroupllc.online', 'kalievmihailo@yandex.ru', 'ndv78@mail.ru', 'ohrana@finvestservice.ru', 'procurementasistantcarmel@gmail.com', 'sale08@qd-xinghe.com', 'sales@thebusinessmail.com', 'turphosase58@yandex.ru']
    actual_emails = sorted(list(set([clean for _, clean, _ in ioc_data.get('Email', [])])))
    assert actual_emails == expected_emails
    
    # SHA256
    expected_sha256 = ['01e4135b70712f8222b270b788b755fbda372f56edc8997c0c363dcf541873c7', '06bdf7cc1314e3739e4da44a58249e368a9e918acaa9b0ce8f488d1c11274c92', '0fe0d4da02aa573aaa4a7cf455300e75b9aaf1e126a91652dba84ff986b99307', '173bd2fc717b38527a57fad443aac11c49aef61f5f84e175872db53a99d2fd4e', '1842edc874b881ef3d7cd652a5dba4131712afc9fd5b7fce0bbfdc9a410faf9e', '1a4339229d831620e3b1413c9069a50949af84a332a0b705430a7a08f38837e5', '1beba7bcaf594abc134967d46daba76c2b554b2358df3e1b6dcc993e336e6490', '2787956c2a7e3723c7729ac1fe4f249a9dc194246554249c6e5526c273fb7042', '28acd5fff4c51495343dfae11f287f5237aadcd7e2777346bdfdb54025b3da37', '3057ec5b6ca4841b13739f936a428edbd671bf26bf1fae4ff52ebd677bd82c50', '30d2b1f4ba9373a0ce7a680ff08e13f084880f5f47a6b8e577222a79ae21b04d', '34c7267370c91020590a49e861660c388fdd453e17d34849734295e02afefd1c', '3774c53aca05c170b5c22c787e7693ae216af823426c3bf46a34043c809b602a', '3b97b802f4376288184d8e5d3dc7f7691de98ce36052047b63189541b492e2a9', '3be0d7880800042d6f4aca2472befec3330d91581ecbf1fbe547fcfdd6e7b5d5', '3bea60b226e676d1da97c01b675500089259a926845a93b71df9dc24f59d5053', '490d4567536b601988039e7d24726337fb8dce8871cc39067bc2a2e9575f886d', '4f3d469af5755c122b73cb0b03acee13ea08b4863621fc0ea121c049a05a8806', '513e79e43a92f59544bfbcfd0953aaadb4cf330e94c054afb465de5988feb735', '5373ab86ceeab08fabe076737f4dfc00362048c6bbf329604bdfbe97497a4fab', '5519c1c8b2fbeec052b6646b7a1fdffc0fcab6083db11ef2529862add61d638e', '5cc5e2d2a89be652f7389dd7fe1d824b0f85c078e45f56ff70f8df5515500248', '663d75063f6d06f7f8679051042fc9e6557d1532d484e1635c040a87a8b999a3', '7342988689d731203018dcda74937b54d614323a1dc43cf85d3239b9f62c1ae4', '79fc11e6ed88637cd432f69056e1c372fd31d0722ce24c19f4cb5131e1574b66', '7eb01ca49e6e5172d3866625c18b327557531983c52a8560976a23f39b72fe24', '815bff7088483befe75c2df2db29da4d982b16917f4ff853fa15d5284349bf73', '844abcc08b3576ea64b732efbd69dc5e86e3fe25850f1773f827f397585487dd', '8a5175036316cf8fd92551b400a3b062c6e48e0da3cda66dcf95ab2305aa8dfe', '8cd11fabe9e8c095ff613046624d8efebaff1bafe6cffcbefbf03996f94f9006', '8fa4c7d17970cf92b74ee61b5e80b60e887b4b2648b485cbe1100ea1b5556357', '933316addde3a7bbc9b6f2a793e4ce7558b32176e7af5fa8e9b0a6d7bae81d68', '93b27c20a350438c5a232a5fcc9801d39047b03e1b9149d5c0655d8b8cd6d7af', 'a14b8a7ebfb7c1b394c786ea7dabe407d0be35b903df11b3642a86012ee49459', 'a2001892410e9f34ff0d02c8bc9e7c53b0bd10da58461e1e9eab26bdbf410c79', 'a94b244f7ee97e701fa78317dfaaf2d55cb85b99c1ca921a651202aa4ac2b3cb', 'b02a0461bf45284fd12e91f293d5b9a21b0e1e77250e0191d0ef659a7430ba5e', 'b554667949dc3847c3f04642b6c7b8d24948b72d5d3f0ee4ac656aa34a3dc8ed', 'bb4e10c087d83f673e41b0fc0a8e17a8caaadeb8ef1e05b9f9bc220192f2803c', 'be1a99859926493699efc488b0076c5f64239f935f2e369b963866ed95b39098', 'be7076eb75e566b3d9005e4e62cbb3ce48eaf6e3553680367ed1f92ea78099ce', 'be8345855016b942a6169ad1956c4113c4001172877a8675f8f0411509d7b468', 'c16a8258cd2af129e8284b33f81a84e950fda4efc74d8fa19fc918f0f7bb3024', 'c86991b83038cf74f4ffeab7db2f2873328a44d50f38d49a30b5ecfda523b308', 'cb185e1d2db1e1f6d6359234afe481618f201745afbf35f7dd629dd90bc303ea', 'cc6b885b8af7d3ca9cfdd537d5923881a761af637098e75cbb4347924e1b3e40', 'da7886379bf4f7106ed5081fc78ac2b59b96a62cefc4abb20aa68ca9fb63ec11', 'e4a07b7d015da2bca35cc5af0b33ae0e388d3756b3e46ac9ad897a6ea6315f7e', 'e4c5a5dd0c918e1735a670b8f7164c3619332083b2074a6f6105303ffe83f70d', 'e71bced33c4b3ae3da623e020ffce573f241cf3486318e4a29e70a8f1901e86b', 'e7562cf6a40504db3c0a6fecef27cf39901be33c9d3031cbc6056fe848ae9714', 'f46863004263c2004ca64e07b7231e91cc5203e60bab8ee0cb6be7d1a1605fdf']
    actual_sha256 = sorted(list(set([clean for _, clean, _ in ioc_data.get('SHA256', [])])))
    assert actual_sha256 == expected_sha256

    # File
    expected_files = []
    actual_files = sorted(list(set([clean for _, clean, _ in ioc_data.get('File', [])])))
    assert actual_files == expected_files


def test_parse_folder_3_fstek():
    """Тест ФСТЭК набора в папке 3."""
    controller = AppController(SETTINGS_JSON)
    controller.set_mode("fstek")
    
    folder_path = os.path.join(TEST_DOC_ROOT, '3')
    docx_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.docx') and not f.startswith('~$')]
    controller.selected_files = docx_files
    
    success, ioc_data = controller.process_files()
    assert success is True
    
    # BDU
    expected_bdus = [('BDU:2025-15156', '240 93 7415.docx')]
    actual_bdus = sorted(list(set(controller.last_bdu_data)))
    assert actual_bdus == expected_bdus
    
    # IP
    expected_ips = ['103.135.101.15', '128.199.194.97', '176.117.107.154', '178.16.55.121', '185.247.224.41', '185.91.127.62', '185.91.127.92', '188.214.39.243', '194.14.217.146', '213.209.157.78', '23.226.71.197', '23.226.71.200', '23.226.71.209', '45.153.127.226', '49.51.230.175', '91.132.94.58']
    actual_ips = sorted(list(set([clean for _, clean, _ in ioc_data.get('IP', [])])))
    assert actual_ips == expected_ips
    
    # DNS
    expected_dns = ['alfalive.ru', 'auditok.org', 'bloggoversikten.com', 'dn710107.ca.archive.org', 'files.qaubctgg.workers.dev', 'ia801706.us.archive.org', 'keep.camdvr.org', 'mail.miniorangeman.com', 'mail.purewater-int.com', 'maxxdns.cfd', 'miniorangeman.com', 'nashglavbuh.org', 'pool.hashvault.pro', 'rex-technolagie.com', 'royal-boat-bf05.qgtxtebl.workers.dev', 'svet-audit.com', 'tr.earn.top', 'velo.qaubctgg.workers.dev', 'www.mubrn.com', 'www.tmtransport.org']
    actual_dns = sorted(list(set([clean for _, clean, _ in ioc_data.get('DNS', [])])))
    assert actual_dns == expected_dns
    
    # URI
    expected_uris = ['http://103.135.101.15/wocaosinm.sh', 'http://128.199.194.97:9001/runnv.tar.gz', 'http://128.199.194.97:9001/setup2.sh', 'http://128.199.194.97:9003/setup2.sh', 'http://172.237.55.180/b', 'http://172.237.55.180/c', 'http://176.117.107.154/bot', 'http://193.34.213.150/nuts/bolts', 'http://193.34.213.150/nuts/x86', 'http://216.158.232.43:12000/sex.sh', 'http://23.132.164.54/bot', 'http://31.56.27.76/n2/x86', 'http://31.56.27.97/scripts/4thepool_miner.sh', 'http://38.165.44.205/1', 'http://38.165.44.205/k', 'http://39.97.229.220:8006/hxxd', 'http://41.231.37.153/rondo.aqu.sh', 'http://41.231.37.153/rondo.arc700', 'http://41.231.37.153/rondo.armeb', 'http://41.231.37.153/rondo.armebhf', 'http://41.231.37.153/rondo.armv4l', 'http://41.231.37.153/rondo.armv5l', 'http://41.231.37.153/rondo.armv6l', 'http://41.231.37.153/rondo.armv7l', 'http://41.231.37.153/rondo.i486', 'http://41.231.37.153/rondo.i586', 'http://41.231.37.153/rondo.i686', 'http://41.231.37.153/rondo.m68k', 'http://41.231.37.153/rondo.mips', 'http://41.231.37.153/rondo.mipsel', 'http://41.231.37.153/rondo.powerpc', 'http://41.231.37.153/rondo.powerpc-440fp', 'http://41.231.37.153/rondo.sh4', 'http://41.231.37.153/rondo.sparc', 'http://41.231.37.153/rondo.x86_64', 'http://45.32.158.54/5e51aff54626ef7f/x86_64', 'http://45.76.155.14/vim', 'http://51.81.104.115/nuts/bolts', 'http://51.81.104.115/nuts/x86', 'http://51.91.77.94:13339/termite/51.91.77.94:13337', 'http://59.7.217.245:7070/app2', 'http://59.7.217.245:7070/c.sh', 'http://68.142.129.4:8277/download/c.sh', 'http://89.144.31.18/nuts/bolts', 'http://89.144.31.18/nuts/x86', 'http://dn710107.ca.archive.org/0/items/msi-pro-with-b-64_20251208_151', 'http://gfxnick.emerald.usbx.me/bot', 'http://help.093214.xyz:9731/FF22', 'http://help.093214.xyz:9731/fn32.sh', 'http://keep.camdvr.org:8000/BREAKABLE_PARABLE5', 'http://keep.camdvr.org:8000/d5.sh', 'http://meomeoli.mooo.com:8820/CLoadPXP/lix.exe?pass=PXPa9682775lckbitXPRopGIXPIL', 'http://vps-zap812595-1.zap-srv.com:3000/sex.sh', 'https://api.hellknight.xyz/js', 'https://api.qtss.cc:443/en/about?source=redhat&id=v1.0', 'https://api.qtss.cc:443/en/about?source=redhat&id=v1.1', 'https://api.qtss.cc:443/en/about?source=redhat&id=v1.2', 'https://bloggoversikten.com/local/src.ps1', 'https://bucketadd.org/images/logo.png', 'https://cdn.tagbox.io/assets/6939ddbee4f7fe0011781587/7697c827-2ad6-4f', 'https://dn710107.ca.archive.org/0/items/msi-pro-with-b-64_20251208_15', 'https://gist.githubusercontent.com/demonic-agents/39e943f4de855e2aef12f34324cbf150/raw/e767e1cef1c35738689ba4df9c6f7f29a6afba1a/setup_c3pool_miner.sh', 'https://hakeowner.org/images/ui.png', 'https://ia801706.us.archive.org/25/items/msi-pro-with-b-64_20251208/M', 'https://pastebin.com/raw/RUEv8DRU', 'https://rex-technolagie.com/arquivo_20251209004659.txt', 'https://stoaccinfoniqaveeambkp.blob.core.windows.net/veeam', 'https://teacoffeepremix.in/arquivo_20251209173358.txt', 'https://teacoffeepremix.in/arquivo_20251211005729.txt', 'https://tr.earn.top/Log.php', 'https://tr.earn.top/apaches.sh']
    actual_uris = sorted(list(set([clean for _, clean, _ in ioc_data.get('URI', [])])))
    assert actual_uris == expected_uris
    
    # SHA256
    expected_sha256 = ['00714292822d568018bb92270daecdf243a2ca232189677d27e38d632bfd68be', '013041d5a4a13a5b2703b28dce68920fd00f078fa02a09b7e293485c0fb16ab8', '054a22279de7a8c0fd75a72b39648dd2429bef07c268756087ed96792dde4a4c', '0575bd21aa78960eb4c1118d56dcdfe5fdaf6c12d3d1b3e7c66311a26e383588', '05e578a967168b704d8bdcba95a8d69fdda25854263e037990add05ccb403115', '0640bf6377ec676b1f412a18ac37f5de6c7fcd237d3c27aad774cebeed31e4e2', '0a6376107abdf30ea14f4bdaf785b2db7d18e0818bd332511dcce3824b8a42b6', '0c748b9e8bc6b5b4fe989df67655f3301d28ef81617b9cbe8e0f6a19d4f9b657', '0f017be8d45171f9aab9ce45821decc216fbfa6f3d273fc3430b40f017efd9f7', '0f0f9c339fcc267ec3d560c7168c56f607232cbeb158cb02a0818720a54e72ce', '0f2926f800dd1b460f839f11b7226449e369791caca40b7b0e047dd1273a0da9', '108e284401cd4078563bf6b49b5aa6eaed292f20f93bbf8ebbb1a5423c77c5d5', '13cfe3fd5a544dbed0b3293db0303a4ecbd81eecad53b511f28dfbbf25f156cf', '13d7380344bf1f9e17e8970c01127a2fe2528d3e640b36ef478ccd4024033411', '14b85b07bfdd134e709ff973871d75d33ecca964457373b76b34a70183c2b1d0', '14ee3eb58cc5e6c6f36461058a0711d10de694f670c4114ce6327cd0c95d4942', '1bd71ea3b9409a6e86fac12039258f8ed8b59261ff2509673544e4a548987931', '2695e26637dbf8c2aa46af702c891a5a154e9a145948ce504db0ea6a2d50e734', '2aa029088c04eb10b056c18fcc39395936e6f01ee9ebdeed2558e4899116ee86', '2c34d8fc0881d3cd4fb693fc5fe2edf405b8424174d3dbb800385fd70969f39d', '2c39766881566d535433138192309534f29c1335e864f954b17c4d18f6bebf42', '2cd41569e8698403340412936b653200005c59f2ff3d39d203f433adb2687e7f', '2e3df3649aba74f4fce04c7323d612642a409ae8944530f5e36b1bac1c38a9d7', '324b9ad3a186b3e11bddfa05994b88eca3719e5c1999aa50430d808c4ba2b6d5', '34b2a6c334813adb2cc70f5bd666c4afbdc4a6d8a58cc1c7a902b13bbd2381f4', '35fbedfafa9a2267d8eab711ce0e9db66dca304a4b4379d7a965ce3893b51fc1', '37f307b378c028afa67a236a05224e367ed486ab3ab2f7c3e13518d0823e137d', '3854862bb3ee623f95d91fa15b504e2bbc30e23f1a15ad7b18aedb127998c79c', '4d0517229ef88f2410a2a1983eaf4036872911c8cf31c3ceb38c11210d02e91e', '55c07dd40ffcf07d569b8b762513cdbfc51e7a4c77ce6613524794515b7d6682', '5a56319605f60380b52aecba1f1ee6026c807d55026b806a3b6585d5ba5931bd', '5dcde82f7a2db50dddf9b42dab3e3affabedfe237d7c956a1de660a702fa74b6', '5e4085553f083d1fd31d673f0746670dfc1f9ebb9911f2fe754e59d9ca6176dc', '5ea192181fcb596b9782457c11433fba5899169e97d7a9b2c0f658407e2ec095', '61598b986aeaeb24d7565a7bb3a113e61f88b4d4c6169d2bd7fd0b988d3e41c9', '649bdaa38e60ede6d140bd54ca5412f1091186a803d3905465219053393f6421', '65d840b059e01f273d0a169562b3b368051cfb003e301cc2e4f6a7d1907c224a', '66a01192355a1ee15a0ceafacbf3bf83148813f67ba24bdfc5423e4fcb4e744f', '66fcc7248cdfc2babd78b71925f6570e436de37d5589b47a534e3edc7bcab59d', '67687b54f9cfee0b551c6847be7ed625e170d8bb882f888e3d0b22312db146cd', '6f79ee17dbb75d1ed7e0535a7b498c2249d538c0836d6ecee16fec491b200ce9', '70c4f474516adb9bba17759bf2023ad445fe8910fa83cdcc225b14a8ccb6fb69', '746f2d5d727511c1bd1ad936f35ac0851a520aadcf201f0d5e23dc6cd728dd4a', '74d70f53748125eb4439cb790817fb1d0e9159f75c7dd5148444f507ba6dee1d', '776850a1e6d6915e9bf35aa83554616129acd94e3a3f6673bd6ddaec530f4273', '79daa001c67dc83bdd6189417ccf4bf83ea5da4c6211bbac91c1d7d55f76fa5f', '7c466c9c15a125fabe401d51195cb8760cefc120c5ad52a3b9489eb391fc4518', '7c9554c18a6b8fe87a570dd5cd5a0f041a782fc2424ab02ac675e474e2e0a9ce', '7e0a0c48ee0f65c72a252335f6dcd435dbd448fc0414b295f635372e1c5a9171', '7e7455cbdca4a9af0e9c4fba21b8feed7967658bb72624747737ea23673ec37d', '7f5bad67cec7492b023ca08e8fa3ed5db9eb186fab0472b34993fe3cb96383be', '85296ee0d867175da1b790f472824f6e702930676aa9b41c4f40f62f41e91652', '85844ae7394f2cf907b6378b415e77f7e29069c7e791598cf0985adf4f53320e', '858874057e3df990ccd7958a38936545938630410bde0c0c4b116f92733b1ddb', '860acd2b9aec21cf03e1c5ec8f79b1ef4e7b78eb9ba7a6c0a915586957356aea', '8d73ee0b2713fa728a154c12ba71b13197484a4db7c0a2c6cd9f3076f1823624', '90f24d6175e1b5fac4e2844e77554ff03dec2174f18c07c008699af540fe2788', '93e75eada1b8f155bdb41c1af0f7d7ea390b280c6f49c8834c11af2e8f6c3a1c', '94b93f4540f01956895a74d2c0b54e502f2be299e4d2ea0a3cc639619377f229', '96397b3ceb57ed2612f77c5a1c0dd809af27b8c3b1ce600e11ae50ac0450b969', '96c54665cda4f04e9ff60faebcd993d0cf98988258249d9e00fe563be7923899', '9bf659a582b7707bf1ef10bb0578843b52be11b1c9939ae6b48aeea3a82c5dd5', '9d33b5c8830d3fa500b9a95ee44f21ac883de60852064330d7cfdc8c3a9ab662', '9dd0e7dccc7105a30b3a71f10126be4ee5a8e770e743fc4f0bbea0e45cafb39f', '9e6dd8dbcedfbb1d4ef27760196014046418a5b31d93d33fd06ed1190952dcf8', '9e82fe6322585d613c8409fa445394e2e38f24ef85733b8dafcfa3ce8dc23517', '9ec3c31ca3bcdd4597d3e928e36fb0202a5111da7e5d169c58bd97b4ae61ee38', '9f456f3125d7f6ce907e13ec637b9b8c6e4a43b1c9f352d233cfebbc2d0fff32', 'a38b91c061157011a00d29c5e3169fbf2b29c0b0cacc0153dc0cf9918e92c9b7', 'a3b061300d6aee6f8c6e08c68b80a18a8d4500b66d0d179b962fd96f41dc2889', 'a536d755313ce550a510137211eca6171f636fb316026e9df8523c496c8fcd12', 'a57dd44b7bc6233496657867cf053199213289f58c1c3c8d4eb565ed3707deb1', 'a605a70d031577c83c093803d11ec7c1e29d2ad530f8e95d9a729c3818c7050d', 'aaf8258585d086cce588a3e870eb485270ee135087eee9ef8766db9f86677ecd', 'ae4991476ed082920e674457f4eceb71367265f4d2150b89214abceb9ebf2407', 'b1034a328855aadadf35f083ce9b2357a6700d2a07a730b10f66ab410fd0c1bb', 'b67221d6057a2a08bd19cdebf22e6d5557a8794463413e6fc128c7ec15a41415', 'c3e806dbf5f01d8d04918c1e734ccce59b6b6057f13dfd77e2c6745442c3c7c1', 'c70fafe5f9a3e5a9ee7de584dd024cb552443659f06348398d3873aa88fd6682', 'c79fcb6c433d8a613f25b9b4c81c1c2514ac97e9aaae7c7c84a432b2476b5e4e', 'c8a8c7e21136a099665c2fad9accb41152d129466b719ea71678bab665e03389', 'cc17c5a982a899986c292a41cdc0dfe75b7126b4833521a9b010722a382d11e8', 'd17bf1c3d50bf4acba18418b0cdcc524be268848b15542e4895a74dd0e4606fb', 'db38b69a3444f00035ac36b2a82f7fc4c9bc9d30428100d7805016961b3253ee', 'dca90d7d9e5770acbd991af69bafa80fe596430c29c78d5036a8fb08ff900e12', 'dee2b2da6b917d2dc7d3dcbbd3c505dd4f128c07059659f9e891000faef2512c', 'dfd49ea1911fb7e800440c82b6518828ec7fa7c595d7ea6baabec29e5d9cecec', 'e19ae27f03c252d4e7b44c462a4edaa1ae759888bcd25cb7863c3c08c35936f1', 'e22fb0c295eefaeb4b25a0b9038a0c60cec9389b894fa22902a7122ddb8779a2', 'e60298307befa4b22eeedef02019a39c93729567fcd4a7745350fd27a92538bd', 'e6562a37dd58030126408186ce66c1b33d406e9cbd22abe0ff023e43e4e3a123', 'ea4a453be116071ab1ccbd24eb8755bf0579649f41a7b94ab9e68571bb9f4a1e', 'ea8c8f834523886b07d87e85e24f124391d69a738814a0f7c31132b6b712ed65', 'ec750acffc7d178d9311b8c19daa83f4c7f1742e6869e7ecd4a0d8d511971c63', 'ed4a064ef099e0ea40faf4b1e3618f20c52833b148ae578f80f09eabd2d6acd2', 'f4d042deb2f8ffaea535884cfaaf7435bb1763c95cf4df89c8771b710ed1f2d8', 'f749d534e3aa7d6c803b57e422a729d774ef74ff4be0131e2a77b19bbcd9c87c', 'f85423686b42f94c9d76412b104a98f7b03572d6fcf2392caa55322ee97d4a81', 'f9b3d9dec0c31e8e62457b852380beeb350f4b5c8d8d32c6c0c7efbce2b77d51', 'fa9afc9336029a3070ca4dfb5b2511b64bc3cc160daa6911587a01f4c9841894', 'fe23d51146aed580bd35ec18c525e7efc68832169328691e989b8870b70de0ce']
    actual_sha256 = sorted(list(set([clean for _, clean, _ in ioc_data.get('SHA256', [])])))
    assert actual_sha256 == expected_sha256
    
    # MD5
    expected_md5 = ['022287b05e4c5ba5503f2b798219f5e9', '0287ba0ecc176ae63ea1d1e053654f32', '1100e1d599b5e4f87082670673c8abfb', '15c839292684ac6374633d231dbd76a7', '17134fe1344744cf99a93483f6859212', '22573d874ac9ffa785e57d94e243b48d', '391f30807d3cf333cdc286d1ff5b0f58', '3eb0b0811c0ab9e87e2ee7f7bac7c46a', '4395e8e7351de03faac54492ee2bc874', '5e7b3664311b2daa9ee040b3cff4d82f', '77dc27fb2ed18f3977241e9475097746', '7b00beb5a7ef4a142ebcdcc052b312a3', '84533ef6651f38fe162ad2753f1ad788', '86a164a403a94c8ccd4f0ba383fa943c', '8762fcdf43a2080ff52348b856169a2d', '906e49f334041ebccc071985ecdcf2ba', 'b44a3229ab54f7367ee2acd678bec2d5', 'bd6b6210241be8850c29ea8476ed9534', 'd69989f700c8f5575bb77559807bfc5f', 'ddd06131fa8b705c3c9439ee462741ae', 'e0b008ea6eef411ed6f9faab8f1d3bee', 'f6b126c83ea4a63f277199d7c06617d6']
    actual_md5 = sorted(list(set([clean for _, clean, _ in ioc_data.get('MD5', [])])))
    assert actual_md5 == expected_md5

    # File
    expected_files = [
        "1.zip",
        "1930 xlsx.z",
        "225840316.exe",
        "225840316.pdf .rar",
        "225840316.xlsx .z",
        "Contract.bz",
        "Contract.vbs",
        "payment.bz",
        "payment.vbs",
        "Акт cвepки взaимopacчeтoв пpeдпpиятия № 253 oт 8 декабря 2025 гoдa.exe",
        "Бланк.doc",
        "Документ.pdf.lnk",
        "Документ.zip",
        "Предложение коммерческое Орион №562 от 04.12.2025.scr",
        "Предложение коммерческое Орион №562 от 04.12.2025.zip"
    ]
    actual_files = sorted(list(set([clean for _, clean, _ in ioc_data.get('File', [])])))
    assert actual_files == expected_files


def test_sequential_status_detection_and_parsing_details():
    """Тест новой логики последовательного статуса, списков ФСТЭК и сохранения скобок в именах файлов."""
    from ioc_analyzer.core.parser import IOCParser
    
    ioc_config = [
        {"name": "IP", "enabled": True, "regex": r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:\[\.\]|\.)){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"},
        {"name": "File", "enabled": True, "regex": r"(?:\«)([^\«\»]+?)(?:\»)"},
        {"name": "SHA256", "enabled": True, "regex": r"\b[a-fA-F0-9]{64}\b"},
        {"name": "MD5", "enabled": True, "regex": r"\b[a-fA-F0-9]{32}\b"}
    ]
    
    # 1. Тест последовательного определения статуса в ГосСОПКА секциях
    parser_gossopka = IOCParser(ioc_config, mode="gossopka")
    
    section_text = (
        "Для поиска и блокировки:\n"
        "1.1.1.1\n"
        "Для поиска:\n"
        "2.2.2.2\n"
        "Для разблокирования:\n"
        "3.3.3.3"
    )
    
    res = parser_gossopka.find_all_raw_matches_with_spans(section_text)
    all_matches = []
    for ioc_type, ioc_list in res.items():
        for original, cleaned, start, end in ioc_list:
            all_matches.append((ioc_type, original, cleaned, start, end))
    all_matches.sort(key=lambda x: x[3])
    
    statuses = []
    n = len(all_matches)
    for i in range(n):
        ioc_type, original, cleaned, start, end = all_matches[i]
        prev_end = all_matches[i-1][4] if i > 0 else 0
        next_start = all_matches[i+1][3] if i < n - 1 else len(section_text)
        
        before_context = section_text[prev_end:start].lower()
        after_context = section_text[end:next_start].lower()
        
        status = None
        if 'разблокиров' in before_context or 'разблокира' in before_context or 'легитимный' in before_context:
            status = "unblock"
        elif 'для поиска и блокировки' in before_context:
            status = "block"
        elif 'для поиска' in before_context:
            status = "search"
        elif 'блокиров' in before_context:
            status = "block"
            
        if status is None:
            if 'разблокиров' in after_context or 'разблокира' in after_context or 'легитимный' in after_context:
                status = "unblock"
            elif 'для поиска и блокировки' in after_context:
                status = "block"
            elif 'для поиска' in after_context:
                status = "search"
            elif 'блокиров' in after_context:
                status = "block"
        if status is None:
            status = "block"
        statuses.append((cleaned, status))
        
    assert statuses == [
        ("1.1.1.1", "block"),
        ("2.2.2.2", "search"),
        ("3.3.3.3", "unblock")
    ]
    
    # 2. Тест пре-парсинга списков ФСТЭК и продолжения обычного парсинга
    parser_fstek = IOCParser(ioc_config, mode="fstek")
    fstek_text = (
        "Рекомендуется заблокировать хэш-суммы по спискам:\n"
        "30a555a0aad7d370fac2f812a062f6bbbec671c46c1457a759e25945d3539b94; "
        "5169a14a85833911e25934854f74f644926a1498cdc4ee9f2aeaf167c7995f8b.\n"
        "Также был обнаружен IP 8.8.8.8 и файл «test_file [множество пробелов].exe»."
    )
    
    file_ioc_results = parser_fstek.find_all_raw_matches_with_spans(fstek_text)
    
    sha256_cleaned = sorted([x[1] for x in file_ioc_results.get("SHA256", [])])
    assert sha256_cleaned == [
        "30a555a0aad7d370fac2f812a062f6bbbec671c46c1457a759e25945d3539b94",
        "5169a14a85833911e25934854f74f644926a1498cdc4ee9f2aeaf167c7995f8b"
    ]
    
    ips = [x[1] for x in file_ioc_results.get("IP", [])]
    assert ips == ["8.8.8.8"]
    
    files = [x[1] for x in file_ioc_results.get("File", [])]
    assert files == ["test_file [множество пробелов].exe"]

