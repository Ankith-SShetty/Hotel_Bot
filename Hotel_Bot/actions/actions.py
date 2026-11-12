from typing import Any, Text, Dict, List
from datetime import datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import os
import random
import time
import uuid
import mysql.connector


def get_latest_entity_value(tracker: Tracker, entity_name: Text) -> Text:
    for event in reversed(list(tracker.events)):
        if event.get("event") == "user":
            for entity in event.get("parse_data", {}).get("entities", []):
                if entity.get("entity") == entity_name:
                    return entity.get("value")
    return None


def normalize_date(date_str: Text) -> Any:
    """Convert common date strings (DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD) to date object."""
    if not date_str:
        return None
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


class ActionSearchHotels(Action):
    
    def name(self) -> Text:
        return "action_search_hotels"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the place entity from the conversation
        place = next(tracker.get_latest_entity_values("place"), None)
        
        # Hotel database for different cities
        city_hotels = {
            "berlin": [
                "Premier Inn Berlin Alexanderplatz – centrally located near Alexanderplatz with good transport links.",
                "Motel One Berlin‑Alexanderplatz – design-budget hotel near Mitte, good value.",
                "MEININGER Hotel Berlin Mitte Humboldthaus – modern, affordable stay in the city centre.",
                "Hotel Berlin, Berlin – another option listed among budget-friendly hotels in Berlin.",
                "Hampton by Hilton Berlin City Centre Alexanderplatz – a slightly higher tier but still appears in cheap hotel listings.",
            ],
            "munich": [
                "Motel One München Sendlinger Tor – in Old Town, good design for budget.",
                "Arthotel Munich – listed among cheap hotels in Munich.",
                "Hotel Am Moosfeld – budget-friendly hotel in listings.",
                "H2 Hotel München Olympiapark – budget option near Olympiapark.",
                "THE 4YOU Hostel & Hotel Munich – value stay, mix of hostel + hotel features.",
            ],
            "münchen": [
                "Motel One München Sendlinger Tor – in Old Town, good design for budget.",
                "Arthotel Munich – listed among cheap hotels in Munich.",
                "Hotel Am Moosfeld – budget-friendly hotel in listings.",
                "H2 Hotel München Olympiapark – budget option near Olympiapark.",
                "THE 4YOU Hostel & Hotel Munich – value stay, mix of hostel + hotel features.",
            ],
            "hamburg": [
                "Superbude Hotel Hamburg St. Pauli – stylish budget hotel in the St. Pauli area.",
                "ibis budget Hamburg City Ost – centrally located, budget category.",
                "B&B Hotel Hamburg‑Altona – a good value stay in Altona.",
                "Motel One Hamburg‑Alster – design hotel but often budget-friendly.",
                "MEININGER Hotel Hamburg City Center – budget hotel chain with good reviews.",
            ],
            "cologne": [
                "art'otel Cologne, Powered by Radisson Hotels – good value and location near the river.",
                "Motel One Köln‑Altstadt – central Altstadt budget stay.",
                "Leonardo Royal Hotel Cologne Bonn Airport – near airport with good budget options.",
                "MEININGER Hotel Köln West – value stay in Köln West.",
                "Premier Inn Köln City Süd – budget choice in City‐Süd.",
            ],
            "köln": [
                "art'otel Cologne, Powered by Radisson Hotels – good value and location near the river.",
                "Motel One Köln‑Altstadt – central Altstadt budget stay.",
                "Leonardo Royal Hotel Cologne Bonn Airport – near airport with good budget options.",
                "MEININGER Hotel Köln West – value stay in Köln West.",
                "Premier Inn Köln City Süd – budget choice in City‐Süd.",
            ],
            "frankfurt": [
                "Premier Inn Frankfurt Messe – located near the Messe/exhibition area, good value.",
                "ibis budget Frankfurt City Ostend – budget option in the Ostend district.",
                "Motel One Frankfurt Messe – good value near city centre and Messe.",
                "Rioca Frankfurt Posto 7 – noted as a budget hotel in Frankfurt listings.",
                "Hotel Hamburger Hof – another budget‐friendly option.",
            ],
            "düsseldorf": [
                "McDreams Hotel Düsseldorf‑City – budget-friendly, good public transport access.",
                "Holiday Inn Express Düsseldorf Airport – near airport and suitable for value stays.",
                "Holiday Inn Express Düsseldorf Hauptbahnhof – centrally located near the main station.",
                "Leonardo Royal Hotel Düsseldorf Königsallee – good reviews for budget segment.",
                "a&o Düsseldorf Hauptbahnhof – simpler budget hostel/hotel hybrid option.",
            ],
            "leipzig": [
                "ibis budget Leipzig City – very budget, 200 m from main station.",
                "McDreams Hotel Leipzig – budget hotel with family rooms near centre.",
                "a&o Leipzig Hauptbahnhof – hostel/hotel mix, very cheap option.",
                "Premier Inn Leipzig City Oper – good budget chain option near central area.",
                "H2 Hotel Leipzig – slightly higher budget tier but still value.",
            ],
            "bremen": [
                "ibis budget Bremen City Center – modern rooms, WiFi included, central.",
                "MEININGER Hotel Bremen Hauptbahnhof – modern budget category near station.",
                "ACHAT Hotel Bremen City – value stay with decent amenities.",
                "Nena Hotel Bremen Mitte – good user ratings in budget category.",
                "IntercityHotel Bremen – also in the budget-range per listings.",
            ],
            "dortmund": [
                "B&B HOTEL Dortmund‑City – affordable and modern near central station.",
                "Hotel Unique Dortmund Hauptbahnhof – budget stay close to train station.",
                "IntercityHotel Dortmund – good value hotel option.",
                "a&o Hostel Dortmund – very budget hostel/hotel hybrid for simpler stays.",
                "Holiday Inn Express Dortmund – budget chain alternative.",
            ],
            "nuremberg": [
                "Motel One Nürnberg Hauptbahnhof – design-budget chain, good value.",
                "Motel One Nürnberg City – another branch in the city with budget pricing.",
                "ibis budget Nürnberg City Messe – central and budget-friendly.",
                "B&B HOTELS Nürnberg‑City – affordable modern hotel with parking options.",
                "Hotel Fackelmann Nürnberg – listed among cheap hotels guests like.",
            ],
            "nürnberg": [
                "Motel One Nürnberg Hauptbahnhof – design-budget chain, good value.",
                "Motel One Nürnberg City – another branch in the city with budget pricing.",
                "ibis budget Nürnberg City Messe – central and budget-friendly.",
                "B&B HOTELS Nürnberg‑City – affordable modern hotel with parking options.",
                "Hotel Fackelmann Nürnberg – listed among cheap hotels guests like.",
            ]
        }
        
        # Fallback: if the place entity was not extracted, try to infer it from the latest user message text
        if not place:
            user_text = tracker.latest_message.get("text", "").strip()
            if user_text:
                user_text_lower = user_text.lower()
                for city_key in city_hotels.keys():
                    if city_key in user_text_lower:
                        place = city_key
                        break

        if not place:
            dispatcher.utter_message(text="I couldn't find the location. Could you please specify the city?")
            return []
        
        # Normalize the place name to lowercase
        place_lower = place.lower()
        
        # Check if we have hotels for this city
        if place_lower in city_hotels:
            hotels = city_hotels[place_lower]
            hotel_list = "\n".join([f"• {hotel}" for hotel in hotels])
            response_message = f"Sure! Here are a few great options you can choose from in {place.title()}:\n\n{hotel_list}\n\nPlease let me know which hotel you'd like to book by saying 'I want [hotel name]' or 'Book the first/second/third hotel'."
        else:
            response_message = f"Sorry, I don't have hotel recommendations for {place.title()} yet. I currently have suggestions for Berlin, Munich, Hamburg, Cologne, Frankfurt, Düsseldorf, Leipzig, Bremen, Dortmund, and Nuremberg."
        
        dispatcher.utter_message(text=response_message)
        return []


class ActionConfirmBooking(Action):
    
    def name(self) -> Text:
        return "action_confirm_booking"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the hotel name from the user's selection
        hotel_name = next(tracker.get_latest_entity_values("hotel_name"), None)
        
        # If no specific hotel name, check if user said "first", "second", "third", etc.
        if not hotel_name:
            user_input = tracker.latest_message.get('text', '').lower()
            place = next(tracker.get_latest_entity_values("place"), None)
            
            if place:
                city_hotels = {
                    "berlin": [
                        "Premier Inn Berlin Alexanderplatz – centrally located near Alexanderplatz with good transport links.",
                        "Motel One Berlin‑Alexanderplatz – design-budget hotel near Mitte, good value.",
                        "MEININGER Hotel Berlin Mitte Humboldthaus – modern, affordable stay in the city centre.",
                        "Hotel Berlin, Berlin – another option listed among budget-friendly hotels in Berlin.",
                        "Hampton by Hilton Berlin City Centre Alexanderplatz – a slightly higher tier but still appears in cheap hotel listings.",
                    ],
                    "munich": [
                        "Motel One München Sendlinger Tor – in Old Town, good design for budget.",
                        "Arthotel Munich – listed among cheap hotels in Munich.",
                        "Hotel Am Moosfeld – budget-friendly hotel in listings.",
                        "H2 Hotel München Olympiapark – budget option near Olympiapark.",
                        "THE 4YOU Hostel & Hotel Munich – value stay, mix of hostel + hotel features.",
                    ],
                    "münchen": [
                        "Motel One München Sendlinger Tor – in Old Town, good design for budget.",
                        "Arthotel Munich – listed among cheap hotels in Munich.",
                        "Hotel Am Moosfeld – budget-friendly hotel in listings.",
                        "H2 Hotel München Olympiapark – budget option near Olympiapark.",
                        "THE 4YOU Hostel & Hotel Munich – value stay, mix of hostel + hotel features.",
                    ],
                    "hamburg": [
                        "Superbude Hotel Hamburg St. Pauli – stylish budget hotel in the St. Pauli area.",
                        "ibis budget Hamburg City Ost – centrally located, budget category.",
                        "B&B Hotel Hamburg‑Altona – a good value stay in Altona.",
                        "Motel One Hamburg‑Alster – design hotel but often budget-friendly.",
                        "MEININGER Hotel Hamburg City Center – budget hotel chain with good reviews.",
                    ],
                    "cologne": [
                        "art'otel Cologne, Powered by Radisson Hotels – good value and location near the river.",
                        "Motel One Köln‑Altstadt – central Altstadt budget stay.",
                        "Leonardo Royal Hotel Cologne Bonn Airport – near airport with good budget options.",
                        "MEININGER Hotel Köln West – value stay in Köln West.",
                        "Premier Inn Köln City Süd – budget choice in City‐Süd.",
                    ],
                    "köln": [
                        "art'otel Cologne, Powered by Radisson Hotels – good value and location near the river.",
                        "Motel One Köln‑Altstadt – central Altstadt budget stay.",
                        "Leonardo Royal Hotel Cologne Bonn Airport – near airport with good budget options.",
                        "MEININGER Hotel Köln West – value stay in Köln West.",
                        "Premier Inn Köln City Süd – budget choice in City‐Süd.",
                    ],
                    "frankfurt": [
                        "Premier Inn Frankfurt Messe – located near the Messe/exhibition area, good value.",
                        "ibis budget Frankfurt City Ostend – budget option in the Ostend district.",
                        "Motel One Frankfurt Messe – good value near city centre and Messe.",
                        "Rioca Frankfurt Posto 7 – noted as a budget hotel in Frankfurt listings.",
                        "Hotel Hamburger Hof – another budget‐friendly option.",
                    ],
                    "düsseldorf": [
                        "McDreams Hotel Düsseldorf‑City – budget-friendly, good public transport access.",
                        "Holiday Inn Express Düsseldorf Airport – near airport and suitable for value stays.",
                        "Holiday Inn Express Düsseldorf Hauptbahnhof – centrally located near the main station.",
                        "Leonardo Royal Hotel Düsseldorf Königsallee – good reviews for budget segment.",
                        "a&o Düsseldorf Hauptbahnhof – simpler budget hostel/hotel hybrid option.",
                    ],
                    "leipzig": [
                        "ibis budget Leipzig City – very budget, 200 m from main station.",
                        "McDreams Hotel Leipzig – budget hotel with family rooms near centre.",
                        "a&o Leipzig Hauptbahnhof – hostel/hotel mix, very cheap option.",
                        "Premier Inn Leipzig City Oper – good budget chain option near central area.",
                        "H2 Hotel Leipzig – slightly higher budget tier but still value.",
                    ],
                    "bremen": [
                        "ibis budget Bremen City Center – modern rooms, WiFi included, central.",
                        "MEININGER Hotel Bremen Hauptbahnhof – modern budget category near station.",
                        "ACHAT Hotel Bremen City – value stay with decent amenities.",
                        "Nena Hotel Bremen Mitte – good user ratings in budget category.",
                        "IntercityHotel Bremen – also in the budget-range per listings.",
                    ],
                    "dortmund": [
                        "B&B HOTEL Dortmund‑City – affordable and modern near central station.",
                        "Hotel Unique Dortmund Hauptbahnhof – budget stay close to train station.",
                        "IntercityHotel Dortmund – good value hotel option.",
                        "a&o Hostel Dortmund – very budget hostel/hotel hybrid for simpler stays.",
                        "Holiday Inn Express Dortmund – budget chain alternative.",
                    ],
                    "nuremberg": [
                        "Motel One Nürnberg Hauptbahnhof – design-budget chain, good value.",
                        "Motel One Nürnberg City – another branch in the city with budget pricing.",
                        "ibis budget Nürnberg City Messe – central and budget-friendly.",
                        "B&B HOTELS Nürnberg‑City – affordable modern hotel with parking options.",
                        "Hotel Fackelmann Nürnberg – listed among cheap hotels guests like.",
                    ],
                    "nürnberg": [
                        "Motel One Nürnberg Hauptbahnhof – design-budget chain, good value.",
                        "Motel One Nürnberg City – another branch in the city with budget pricing.",
                        "ibis budget Nürnberg City Messe – central and budget-friendly.",
                        "B&B HOTELS Nürnberg‑City – affordable modern hotel with parking options.",
                        "Hotel Fackelmann Nürnberg – listed among cheap hotels guests like.",
                    ]
                }
                
                place_lower = place.lower()
                if place_lower in city_hotels:
                    hotels = city_hotels[place_lower]
                    if "first" in user_input:
                        hotel_name = hotels[0]
                    elif "second" in user_input:
                        hotel_name = hotels[1] if len(hotels) > 1 else hotels[0]
                    elif "third" in user_input:
                        hotel_name = hotels[2] if len(hotels) > 2 else hotels[0]
        
        if not hotel_name:
            dispatcher.utter_message(text="I couldn't determine which hotel you selected. Please specify the hotel name or say 'first', 'second', or 'third' hotel.")
            return []
        
        timestamp = int(time.time())
        short_id = timestamp % 100000
        reservation_id = f"HTL-{short_id:05d}"
        
        check_in_date = get_latest_entity_value(tracker, "check_in_date")
        check_out_date = get_latest_entity_value(tracker, "check_out_date")
        number_of_guests = get_latest_entity_value(tracker, "number_of_guests")
        email = get_latest_entity_value(tracker, "email")
        city = None
        for event in tracker.events:
            if event.get("event") == "user" and event.get("intent", {}).get("name") == "inform_place":
                entities = event.get("parse_data", {}).get("entities", [])
                for ent in entities:
                    if ent.get("entity") == "place":
                        city = ent.get("value")
                        break
                if city:
                    break

        if not city and hotel_name:
            hotel_lower = hotel_name.lower()
            if "berlin" in hotel_lower:
                city = "berlin"
            elif any(k in hotel_lower for k in ["münchen", "munich"]):
                city = "munich"
            elif "hamburg" in hotel_lower:
                city = "hamburg"
            elif "cologne" in hotel_lower or "köln" in hotel_lower:
                city = "cologne"
            elif "frankfurt" in hotel_lower:
                city = "frankfurt"
            elif "düsseldorf" in hotel_lower:
                city = "düsseldorf"
            elif "leipzig" in hotel_lower:
                city = "leipzig"
            elif "bremen" in hotel_lower:
                city = "bremen"
            elif "dortmund" in hotel_lower:
                city = "dortmund"
            elif "nürnberg" in hotel_lower or "nuremberg" in hotel_lower:
                city = "nuremberg"

        normalized_check_in = normalize_date(check_in_date)
        normalized_check_out = normalize_date(check_out_date)

        if not normalized_check_in or not normalized_check_out:
            dispatcher.utter_message(text="I couldn't understand the dates. Please provide them in DD-MM-YYYY format (e.g., 11-12-2025).")
            return []

        print(f"[DEBUG] Extracted values: city={city}, check_in={normalized_check_in}, check_out={normalized_check_out}, guests={number_of_guests}, email={email}, hotel={hotel_name}")

        db_host = os.getenv("HOTELBOT_DB_HOST", "localhost")
        db_port = int(os.getenv("HOTELBOT_DB_PORT", "3306"))
        db_user = os.getenv("HOTELBOT_DB_USER", "root")
        db_password = os.getenv("HOTELBOT_DB_PASSWORD", "Ankith@2001")
        db_name = os.getenv("HOTELBOT_DB_NAME", "hotelbot")
        print(f"[DEBUG] DB config for booking insert: host={db_host} port={db_port} user={db_user} db={db_name}")

        try:
            connection = mysql.connector.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database=db_name,
            )
            cursor = connection.cursor()
            insert_query = (
                "INSERT INTO bookings (booking_id, guests, email, checkin, checkout, city, hotel, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"
            )
            values = (
                reservation_id,
                number_of_guests,
                email,
                normalized_check_in,
                normalized_check_out,
                city,
                hotel_name,
            )
            print(f"[DEBUG] Executing insert with values: {values}")
            cursor.execute(insert_query, values)
            connection.commit()
            print(f"[DEBUG] Insert successful. Rows affected: {cursor.rowcount}")
        except Exception as e:
            print(f"Error saving booking to database: {e}")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass
        
        confirmation_message = f"Your booking for hotel {hotel_name} is all set! Here's your reservation ID: {reservation_id}.\n\nPlease keep this ID handy when you arrive.\nDo remember to bring a valid physical ID proof for verification at check-in.\nYour payment will be collected during checkout, so no advance payment is needed right now.\nIs there anything else I can help you with?"
        
        dispatcher.utter_message(text=confirmation_message)
        return []


class ActionGetBookingInfo(Action):
    
    def name(self) -> Text:
        return "action_get_booking_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        booking_id = get_latest_entity_value(tracker, "booking_id")
        if not booking_id:
            dispatcher.utter_message(text="I couldn't detect a booking ID. Please provide it in the format HTL-12345.")
            return []

        db_host = os.getenv("HOTELBOT_DB_HOST", "localhost")
        db_port = int(os.getenv("HOTELBOT_DB_PORT", "3306"))
        db_user = os.getenv("HOTELBOT_DB_USER", "root")
        db_password = os.getenv("HOTELBOT_DB_PASSWORD", "Ankith@2001")
        db_name = os.getenv("HOTELBOT_DB_NAME", "hotelbot")

        booking = None
        try:
            connection = mysql.connector.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database=db_name,
            )
            cursor = connection.cursor(dictionary=True)
            select_query = (
                "SELECT guests, checkin, checkout, city, hotel "
                "FROM bookings WHERE booking_id = %s ORDER BY id DESC LIMIT 1"
            )
            cursor.execute(select_query, (booking_id,))
            booking = cursor.fetchone()
        except Exception as e:
            print(f"Error fetching booking from database: {e}")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass

        if not booking:
            dispatcher.utter_message(text="I couldn't find any reservation with that booking ID. Could you double-check it?")
            return []

        guests = booking.get("guests")
        checkin = booking.get("checkin")
        checkout = booking.get("checkout")
        city = booking.get("city")
        hotel = booking.get("hotel")

        info_message = (
            f"Here are the details for booking ID {booking_id}:\n"
            f"- Guests: {guests}\n"
            f"- Check-in date: {checkin}\n"
            f"- Check-out date: {checkout}\n"
            f"- City: {city}\n"
            f"- Hotel: {hotel}"
        )

        dispatcher.utter_message(text=info_message)
        return []


class ActionSetCity(Action):
    def name(self) -> Text:
        return "action_set_city"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        place = get_latest_entity_value(tracker, "place")
        if place:
            return [SlotSet("city", place)]
        return []


class ActionCancelBooking(Action):
    
    def name(self) -> Text:
        return "action_cancel_booking"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        email = get_latest_entity_value(tracker, "email")
        booking_id = get_latest_entity_value(tracker, "booking_id")

        if not email:
            dispatcher.utter_message(
                text="I couldn't detect your email address. Please provide the email you used for the booking."
            )
            return []

        if not booking_id:
            dispatcher.utter_message(
                text="I couldn't detect a booking ID. Please provide it in the format HTL-12345."
            )
            return []

        db_host = os.getenv("HOTELBOT_DB_HOST", "localhost")
        db_port = int(os.getenv("HOTELBOT_DB_PORT", "3306"))
        db_user = os.getenv("HOTELBOT_DB_USER", "root")
        db_password = os.getenv("HOTELBOT_DB_PASSWORD", "Ankith@2001")
        db_name = os.getenv("HOTELBOT_DB_NAME", "hotelbot")

        rows_affected = 0
        try:
            connection = mysql.connector.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database=db_name,
            )
            cursor = connection.cursor()
            delete_query = (
                "DELETE FROM bookings WHERE booking_id = %s AND email = %s"
            )
            cursor.execute(delete_query, (booking_id, email))
            connection.commit()
            rows_affected = cursor.rowcount
        except Exception as e:
            print(f"Error cancelling booking in database: {e}")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass

        if rows_affected == 0:
            dispatcher.utter_message(
                text="I couldn't find a booking with that email and booking ID. Please double-check your details."
            )
            return []

        dispatcher.utter_message(
            text="Your booking has been successfully cancelled.\nLet me know if you’d like to make a new reservation or need help with anything else."
        )
        return []
