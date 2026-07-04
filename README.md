# TripSense AI

**TripSense AI** is a Google Cloud + NVIDIA accelerated local travel and food itinerary planner.

It helps travellers generate budget-friendly and luxury itineraries using place ratings, review counts, price levels, categories, and local food recommendations.

The project was built for the Hack2Skill APAC GenAI Academy challenge as a practical data intelligence tool that supports faster and better travel-planning decisions.

---

## Problem Statement

Travellers often spend a lot of time manually checking Google Maps, ratings, reviews, food joints, tourist places, prices, and travel preferences before planning a trip.

TripSense AI solves this by converting local place intelligence into a structured itinerary.

A user can enter:

- City
- Number of days
- Budget type
- Food preference
- Travel style

The app then generates a day-wise itinerary with tourist places, lunch/dinner recommendations, place ratings, review counts, and ranking scores.

---

## Real-World Users

TripSense AI can be used by:

- Tourists visiting a new city
- Families planning weekend trips
- Solo travellers
- Local explorers
- Budget travellers
- Luxury travellers
- Travel planners and local guides

---

## Key Decision Supported

The app helps users answer:

> “Where should I go, where should I eat, and how should I plan my trip based on my budget and number of days?”

Instead of manually comparing many places, users get a ranked itinerary generated from structured data.

---

## Features

- Fetches local place and food-joint data using Google Places API
- Stores raw data in Google Cloud Storage
- Cleans and transforms data using Python
- Loads structured data into BigQuery
- Generates budget and luxury itineraries
- Scores places using rating, review count, price level, and category
- Provides a Streamlit web app for itinerary generation
- Provides Looker Studio dashboard for analytics
- Includes CPU vs GPU benchmark scripts
- Uses NVIDIA RAPIDS/cuDF for accelerated dataframe processing

---

## Architecture

```text
Google Places API
      |
      v
Cloud Storage
Raw JSON place data
      |
      v
Python Cleaning Pipeline
      |
      v
BigQuery
Structured place intelligence
      |
      v
Streamlit App
Itinerary generation and recommendation
      |
      v
Looker Studio
Analytics dashboard
      |
      v
NVIDIA RAPIDS/cuDF
Acceleration benchmark


Demo Flow
Open the Streamlit app.
Select city: Jaipur.
Select number of days.
Choose budget type: budget / standard / luxury.
Choose travel style.
Generate itinerary.
View top ranked places.
Open Looker Studio dashboard.
Show CPU vs GPU benchmark results.

TripSense AI is a practical data intelligence tool that helps travellers make faster and better local travel decisions.

It uses Google Cloud for:

Data ingestion
Storage
Analytics
Dashboarding
Deployment

It uses NVIDIA RAPIDS/cuDF for:

Accelerated dataframe processing
Faster scoring
Faster ranking
CPU vs GPU benchmark comparison

The result is an interactive itinerary planner that converts local place data into budget and luxury travel recommendations.