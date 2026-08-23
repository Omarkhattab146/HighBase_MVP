def test_seed_and_health_flow(api_client, generated_store):
    seed_response = api_client.post("/data/seed")

    assert seed_response.status_code == 200
    assert seed_response.json()["products"] == len(generated_store.collections["products"])
    assert api_client.get("/health").json() == {"status": "ok", "data_loaded": True}


def test_clean_endpoint_reports_and_removes_product_quality_issues(api_client):
    response = api_client.post("/data/clean")

    assert response.status_code == 200
    assert response.json() == {
        "processed": 23,
        "cleaned": 21,
        "rejected": 2,
        "duplicates": 1,
        "missing": 1,
        "outliers": 1,
    }


def test_recommendations_honor_limit_price_and_availability(api_client):
    api_client.post("/data/clean")

    response = api_client.post(
        "/recommendations",
        json={"business_type": "Cafe", "query": "coffee", "limit": 3, "max_price": 10},
    )

    assert response.status_code == 200
    recommendations = response.json()["recommendations"]
    assert 0 < len(recommendations) <= 3
    assert all(item["availability"] == "In Stock" for item in recommendations)
    assert all(item["price"] <= 10 for item in recommendations)
    assert any("matches your request" in reason for item in recommendations for reason in item["reasons"])


def test_chat_prefers_message_and_returns_explainable_response(api_client):
    api_client.post("/data/clean")

    response = api_client.post(
        "/chat",
        json={"business_type": "Cafe", "query": "rice", "message": "coffee", "limit": 2},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["request_id"]
    assert body["data_disclaimer"] == "Recommendations use synthetic demo data."
    assert len(body["recommendations"]) <= 2
    assert body["recommendations"]
    assert body["recommendations"][0]["name"] in body["response"]
    assert "Highbase Rice" not in body["response"]


def test_chat_greeting_does_not_trigger_recommendations(api_client):
    response = api_client.post("/chat", json={"message": "hi"})

    body = response.json()
    assert response.status_code == 200
    assert body["recommendations"] == []
    assert "Hello" in body["response"]
    assert body["tools_used"] == []


def test_chat_rejects_questions_outside_highbase_scope(api_client):
    response = api_client.post("/chat", json={"message": "Who won the football match?"})

    body = response.json()
    assert response.status_code == 200
    assert body["recommendations"] == []
    assert body["tools_used"] == []
    assert "only help with HIGHBASE" in body["response"]


def test_chat_returns_structured_offer_and_trend_fields(api_client):
    api_client.post("/data/clean")
    offer=api_client.post("/chat",json={"message":"What offers are available?","limit":5}).json()
    trend=api_client.post("/chat",json={"message":"What products are trending?","limit":5}).json()

    assert offer["intent"] == "offers"
    assert all(item["offer"] for item in offer["offers"])
    assert trend["intent"] == "trends"
    assert all(item["trend_growth"] is not None for item in trend["trends"])


def test_invalid_recommendation_limit_is_rejected(api_client):
    response = api_client.post("/recommendations", json={"limit": 0})

    assert response.status_code == 422
