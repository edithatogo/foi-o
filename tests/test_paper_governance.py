from scripts.paper_governance import audit


def test_paper_governance_fails_closed_without_external_reports():
    result = audit()
    assert result["status"] == "blocked"
    assert "sourceright_auditor" in result["missing_required_reports"]
    assert result["publication_authorised"] is False
