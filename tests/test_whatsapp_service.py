from services.whatsapp_service import WhatsAppService


def test_build_url_does_not_duplicate_brazil_country_code():
    service = WhatsAppService()

    local = service.build_url("11999999999", "oi")
    international = service.build_url("5511999999999", "oi")
    masked = service.build_url("+55 (11) 99999-9999", "oi")

    assert local == "https://wa.me/5511999999999?text=oi"
    assert international == local
    assert masked == local
