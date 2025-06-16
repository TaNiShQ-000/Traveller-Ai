from flask import Flask, render_template, request, jsonify
import random
import json

app = Flask(__name__)

# Load activities from JSON file
try:
    with open('static/activities.json', 'r') as f:
        ACTIVITIES = json.load(f)
except FileNotFoundError:
    ACTIVITIES = []

def filter_activities(themes, travel_month):
    """Filter activities by themes and season."""
    filtered = ACTIVITIES.copy()
    if themes:
        themes_list = [theme.strip().lower() for theme in themes.split(",")]
        filtered = [act for act in filtered if act["type"].lower() in themes_list]
    if travel_month:
        summer_months = ["june", "july", "august"]
        is_summer = travel_month.lower() in summer_months
        filtered = [act for act in filtered if act["season"] == "all" or 
                   (is_summer and act["season"] == "summer") or 
                   (not is_summer and act["season"] == "spring")]
    return filtered

def select_activities(activities, budget, days):
    """Select activities within budget and day limits."""
    selected = []
    total_cost = 0
    max_activities = days * 2
    random.shuffle(activities)
    for act in activities:
        if len(selected) < max_activities and total_cost + act["cost"] <= budget:
            selected.append(act)
            total_cost += act["cost"]
    return selected, total_cost

def arrange_itinerary(selected_activities, days):
    """Arrange activities into daily schedule by area."""
    areas = {}
    for act in selected_activities:
        area = act["area"]
        if area not in areas:
            areas[area] = []
        areas[area].append(act)
    itinerary = {day: [] for day in range(1, days + 1)}
    day = 1
    for acts in areas.values():
        itinerary[day].extend(acts[:2])
        day = (day % days) + 1
    return itinerary

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_itinerary', methods=['POST'])
def generate_itinerary():
    data = request.json
    try:
        days = int(data.get('days', 1))
        budget = int(data.get('budget', 0))
        themes = data.get('themes', '')
        travel_month = data.get('travel_month', '')
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input. Days and budget must be numbers."}), 400

    if days < 1 or budget < 0:
        return jsonify({"error": "Days must be at least 1 and budget non-negative."}), 400

    filtered_activities = filter_activities(themes, travel_month)
    if not filtered_activities:
        return jsonify({"error": "No activities match your preferences."}), 400

    selected_activities, total_cost = select_activities(filtered_activities, budget, days)
    itinerary = arrange_itinerary(selected_activities, days)

    itinerary_data = []
    for day, activities in itinerary.items():
        if activities:
            day_activities = []
            for act in activities:
                day_activities.append({
                    "name": act["name"],
                    "type": act["type"],
                    "cost": act["cost"],
                    "description": act["description"],
                    "image": f"https://source.unsplash.com/300x150/?{act['name'].replace(' ', '-')}"
                })
            itinerary_data.append({"day": day, "activities": day_activities})

    return jsonify({"itinerary": itinerary_data, "total_cost": total_cost})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)