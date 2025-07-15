from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import json

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PRICE_TABLE = {
    'sedan': {'full': (2500, 4500), 'half': (1200, 2500), 'partial': (600, 1500)},
    'coupe': {'full': (2500, 5000), 'half': (1500, 3000), 'partial': (600, 1500)},
    'truck': {'full': (3000, 5500), 'half': (1500, 3000), 'partial': (800, 1800)},
    'suv': {'full': (3200, 6000), 'half': (1500, 3000), 'partial': (800, 2000)},
    'box truck': {'full': (3000, 6500), 'half': (2000, 4500), 'partial': (2000, 4500)}
}

def estimate_quote(vehicle_list):
    total_min, total_max = 0, 0
    for v in vehicle_list:
        vtype = v["type"].lower()
        wrap = v["wrap"].lower()
        qty = v["qty"]
        if vtype in PRICE_TABLE and wrap in PRICE_TABLE[vtype]:
            low, high = PRICE_TABLE[vtype][wrap]
            total_min += low * qty
            total_max += high * qty
    return total_min, total_max

@app.route("/quote", methods=["POST"])
def get_quote():
    user_input = request.json.get("message", "")

    gpt_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "Always respond ONLY in JSON format like this: "
                    '{"vehicles":[{"type":"sedan","wrap":"full","qty":2}, {"type":"truck","wrap":"partial","qty":1}]}'
                )
            },
            {"role": "user", "content": user_input}
        ]
    )

    try:
        content = gpt_response.choices[0].message.content
        structured_data = json.loads(content)
        vehicles = structured_data["vehicles"]
        quote_min, quote_max = estimate_quote(vehicles)
        return jsonify({
            "success": True,
            "quote_range": f"${quote_min:,}–${quote_max:,}",
            "vehicles": vehicles
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
