from tests.conftest import auth_header


def test_login_and_rbac(client):
    r = client.post("/api/v1/auth/login-json", json={"username": "operator", "password": "demo1234"})
    assert r.status_code == 200
    op = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # operator cannot edit thresholds (safety/ops only)
    r = client.put("/api/v1/tanks/1/thresholds", headers=op,
                   json={"parameter": "pressure", "hi_critical": 4.0})
    assert r.status_code == 403

    safety = auth_header(client, "safety")
    r = client.put("/api/v1/tanks/1/thresholds", headers=safety,
                   json={"parameter": "pressure", "hi_critical": 4.0})
    assert r.status_code == 200


def test_bad_credentials(client):
    r = client.post("/api/v1/auth/login-json", json={"username": "operator", "password": "nope"})
    assert r.status_code == 401


def test_ingest_raises_threshold_alarm(client):
    h = auth_header(client, "admin")
    batch = {"readings": [{"tank_code": "TK-101", "flammable_gas_ppm": 150.0, "pressure": 1.2}],
             "score": False}
    r = client.post("/api/v1/readings/ingest", json=batch)
    assert r.status_code == 200
    assert r.json()["alarms_raised"] >= 1

    alarms = client.get("/api/v1/alarms", headers=h).json()
    assert any(a["parameter"] == "flammable_gas_ppm" and a["severity"] == "critical" for a in alarms)


def test_two_person_rule_on_critical(client):
    auth_header(client, "admin")
    client.post("/api/v1/readings/ingest",
                json={"readings": [{"tank_code": "TK-102", "flammable_gas_ppm": 150.0}], "score": False})
    h_admin = auth_header(client, "admin")
    alarms = client.get("/api/v1/alarms", headers=h_admin).json()
    crit = next(a for a in alarms if a["severity"] == "critical")
    assert crit["requires_two_person"]

    # single ack -> cannot clear
    client.post(f"/api/v1/alarms/{crit['id']}/ack", headers=h_admin, json={"note": "seen"})
    r = client.post(f"/api/v1/alarms/{crit['id']}/clear", headers=h_admin)
    assert r.status_code == 403

    # second distinct user acks -> clear allowed
    h2 = auth_header(client, "safety")
    client.post(f"/api/v1/alarms/{crit['id']}/ack", headers=h2, json={"note": "confirmed"})
    r = client.post(f"/api/v1/alarms/{crit['id']}/clear", headers=h2)
    assert r.status_code == 200


def test_optimizer_plan(client):
    h = auth_header(client, "opsmanager")
    r = client.post("/api/v1/optimization/plan", headers=h)
    assert r.status_code == 200
    plan = r.json()
    assert "schedule" in plan and plan["makespan_minutes"] >= 0


def test_audit_chain_intact(client):
    auth_header(client, "safety")  # generates a login audit entry
    h = auth_header(client, "safety")
    r = client.get("/api/v1/admin/audit", headers=h)
    assert r.status_code == 200
    assert r.json()["chain_intact"] is True


def test_compliance_report(client):
    h = auth_header(client, "safety")
    r = client.get("/api/v1/reports/compliance", headers=h)
    assert r.status_code == 200
    assert "api_rp_2350" in r.json()
