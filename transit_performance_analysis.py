import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import warnings
import sys
import os

warnings.filterwarnings('ignore')


def parse_timestamp(timestamp_value):
    if timestamp_value is None:
        return None
    
    try:
        if isinstance(timestamp_value, dict) and "$numberLong" in timestamp_value:
            milliseconds = int(timestamp_value["$numberLong"])
            return datetime.fromtimestamp(milliseconds / 1000.0)
        
        if isinstance(timestamp_value, str):
            if '+' in timestamp_value or timestamp_value.endswith('Z'):
                return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(timestamp_value)
        
        if isinstance(timestamp_value, (int, float)):
            return datetime.fromtimestamp(timestamp_value / 1000.0)
            
    except Exception as e:
        print(f"Warning: Failed to parse timestamp {timestamp_value}: {e}")
        return None
    
    return None


def get_nested_value(data, *keys, default=None):
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current if current is not None else default


def extract_address(address_data, prefix=""):
    if not address_data or not isinstance(address_data, dict):
        return {
            f"{prefix}city": None,
            f"{prefix}state": None,
            f"{prefix}pincode": None
        }
    
    return {
        f"{prefix}city": get_nested_value(address_data, "city", default=None),
        f"{prefix}state": get_nested_value(address_data, "stateOrProvinceCode", default=None),
        f"{prefix}pincode": get_nested_value(address_data, "postalCode", default=None)
    }


def find_pickup_event(events):
    if not events:
        return None
    
    for event in events:
        event_type = get_nested_value(event, "eventType", default="")
        event_description = get_nested_value(event, "eventDescription", default="")
        
        if event_type == "PU" or "pick" in str(event_description).lower():
            return event
    
    return None


def find_delivery_event(events):
    if not events:
        return None
    
    for event in events:
        event_type = get_nested_value(event, "eventType", default="")
        event_description = get_nested_value(event, "eventDescription", default="")
        
        if event_type == "DL" or "deliver" in str(event_description).lower():
            return event
    
    return None


def count_unique_facilities(events):
    if not events:
        return 0
    
    unique_facilities = set()
    for event in events:
        arrival_location = get_nested_value(event, "arrivalLocation", default="")
        if arrival_location and "FACILITY" in str(arrival_location).upper():
            address = get_nested_value(event, "address", default={})
            city = get_nested_value(address, "city", default="")
            postal_code = get_nested_value(address, "postalCode", default="")
            facility_id = f"{arrival_location}_{city}_{postal_code}".strip()
            if facility_id:
                unique_facilities.add(facility_id)
    
    return len(unique_facilities)


def count_transit_events(events):
    if not events:
        return 0
    
    count = 0
    for event in events:
        event_type = get_nested_value(event, "eventType", default="")
        if event_type == "IT":
            count += 1
    
    return count


def calculate_facility_transit_time(events):
    if not events or len(events) < 2:
        return 0.0
    
    sorted_events = []
    seen_timestamps = set()
    
    for event in events:
        timestamp = parse_timestamp(get_nested_value(event, "timestamp"))
        if timestamp:
            base_time = timestamp.timestamp()
            offset = 0
            while (base_time + offset) in seen_timestamps:
                offset += 0.001
            final_time = datetime.fromtimestamp(base_time + offset)
            seen_timestamps.add(final_time.timestamp())
            sorted_events.append((final_time, event))
    
    sorted_events.sort(key=lambda x: x[0])
    
    total_hours = 0.0
    facility_types = {"FEDEX_FACILITY", "ORIGIN_FEDEX_FACILITY", "DESTINATION_FEDEX_FACILITY"}
    
    for i in range(len(sorted_events) - 1):
        current_event = sorted_events[i][1]
        next_event = sorted_events[i + 1][1]
        
        current_location = get_nested_value(current_event, "arrivalLocation", default="")
        next_location = get_nested_value(next_event, "arrivalLocation", default="")
        
        current_address = get_nested_value(current_event, "address", default={})
        next_address = get_nested_value(next_event, "address", default={})
        
        current_city = get_nested_value(current_address, "city", default="")
        current_postal = get_nested_value(current_address, "postalCode", default="")
        next_city = get_nested_value(next_address, "city", default="")
        next_postal = get_nested_value(next_address, "postalCode", default="")
        
        current_facility = f"{current_location}_{current_city}_{current_postal}"
        next_facility = f"{next_location}_{next_city}_{next_postal}"
        
        is_current_facility = current_location and "FACILITY" in current_location.upper()
        is_next_facility = next_location and "FACILITY" in next_location.upper()
        
        if is_current_facility and is_next_facility and current_facility != next_facility:
            current_time = sorted_events[i][0]
            next_time = sorted_events[i + 1][0]
            
            if current_time and next_time:
                hours_between = (next_time - current_time).total_seconds() / 3600.0
                if hours_between > 0:
                    total_hours += hours_between
    
    return total_hours


def count_delivery_attempts(events):
    if not events:
        return 0
    
    count = 0
    for event in events:
        event_type = get_nested_value(event, "eventType", default="")
        event_description = get_nested_value(event, "eventDescription", default="")
        
        if (event_type == "OD" or 
            "vehicle" in str(event_description).lower() or 
            "out for delivery" in str(event_description).lower()):
            count += 1
    
    return count


def is_express_service(service_type):
    if not service_type:
        return False
    
    service_upper = str(service_type).upper()
    has_express = "EXPRESS" in service_upper
    has_saver = "SAVER" in service_upper
    
    return has_express and not has_saver


def process_shipment(shipment):
    if not shipment or not isinstance(shipment, dict):
        return None
    
    tracking_number = get_nested_value(shipment, "trackingNumber", default=None)
    service_type = get_nested_value(shipment, "service", "type", default=None)
    carrier_code = get_nested_value(shipment, "carrierCode", default=None)
    
    package_weight = get_nested_value(shipment, "packageWeight", "value", default=None)
    packaging_type = get_nested_value(shipment, "packaging", "type", default=None)
    
    shipper_address = get_nested_value(shipment, "shipperAddress", default={})
    origin_info = extract_address(shipper_address, "origin_")
    
    destination_address = get_nested_value(shipment, "destinationAddress", default={})
    destination_info = extract_address(destination_address, "destination_")
    
    events = get_nested_value(shipment, "events", default=[])
    
    pickup_event = find_pickup_event(events)
    delivery_event = find_delivery_event(events)
    
    pickup_time = None
    delivery_time = None
    total_transit_hours = None
    
    if pickup_event:
        pickup_timestamp = get_nested_value(pickup_event, "timestamp")
        pickup_time = parse_timestamp(pickup_timestamp)
    
    if delivery_event:
        delivery_timestamp = get_nested_value(delivery_event, "timestamp")
        delivery_time = parse_timestamp(delivery_timestamp)
    
    if not pickup_time:
        dates_or_times = get_nested_value(shipment, "datesOrTimes", default=[])
        for date_time in dates_or_times:
            if get_nested_value(date_time, "type", default="") == "ACTUAL_PICKUP":
                pickup_time = parse_timestamp(get_nested_value(date_time, "dateOrTimestamp"))
                break
    
    if not delivery_time:
        dates_or_times = get_nested_value(shipment, "datesOrTimes", default=[])
        for date_time in dates_or_times:
            if get_nested_value(date_time, "type", default="") == "ACTUAL_DELIVERY":
                delivery_time = parse_timestamp(get_nested_value(date_time, "dateOrTimestamp"))
                break
    
    if pickup_time and delivery_time:
        total_transit_hours = (delivery_time - pickup_time).total_seconds() / 3600.0
    
    pickup_datetime_str = pickup_time.strftime("%Y-%m-%d %H:%M:%S") if pickup_time else None
    delivery_datetime_str = delivery_time.strftime("%Y-%m-%d %H:%M:%S") if delivery_time else None
    
    facilities_count = count_unique_facilities(events)
    transit_events_count = count_transit_events(events)
    facility_transit_time = calculate_facility_transit_time(events)
    
    if total_transit_hours and facilities_count > 0:
        avg_hours_per_facility = total_transit_hours / facilities_count
    else:
        avg_hours_per_facility = None
    
    express_service = is_express_service(service_type)
    
    delivery_location = get_nested_value(shipment, "deliveryLocationType", default=None)
    delivery_attempts = count_delivery_attempts(events)
    first_attempt = (delivery_attempts == 1)
    
    total_events = len(events) if events else 0
    
    return {
        "tracking_number": tracking_number,
        "service_type": service_type,
        "carrier_code": carrier_code,
        "package_weight_kg": package_weight,
        "packaging_type": packaging_type,
        "origin_city": origin_info["origin_city"],
        "origin_state": origin_info["origin_state"],
        "origin_pincode": origin_info["origin_pincode"],
        "destination_city": destination_info["destination_city"],
        "destination_state": destination_info["destination_state"],
        "destination_pincode": destination_info["destination_pincode"],
        "pickup_datetime_ist": pickup_datetime_str,
        "delivery_datetime_ist": delivery_datetime_str,
        "total_transit_hours": total_transit_hours,
        "num_facilities_visited": facilities_count,
        "num_in_transit_events": transit_events_count,
        "time_in_inter_facility_transit_hours": facility_transit_time,
        "avg_hours_per_facility": avg_hours_per_facility,
        "is_express_service": express_service,
        "delivery_location_type": delivery_location,
        "num_out_for_delivery_attempts": delivery_attempts,
        "first_attempt_delivery": first_attempt,
        "total_events_count": total_events
    }


def load_data(json_file_path):
    print(f"Loading data from {json_file_path}...")
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    shipment_records = []
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                track_details = item.get("trackDetails", [])
                shipment_records.extend(track_details)
            else:
                shipment_records.append(item)
    elif isinstance(data, dict):
        if "trackDetails" in data:
            shipment_records = data["trackDetails"]
        else:
            shipment_records = [data]
    else:
        raise ValueError("Unexpected data format")
    
    print(f"Found {len(shipment_records)} shipment records to process...")
    
    processed_shipments = []
    for idx, shipment in enumerate(shipment_records):
        try:
            result = process_shipment(shipment)
            if result:
                processed_shipments.append(result)
        except Exception as e:
            print(f"Warning: Failed to process shipment {idx}: {e}")
            continue
    
    print(f"Successfully processed {len(processed_shipments)} shipments...")
    
    return pd.DataFrame(processed_shipments)


def create_detailed_csv(df, output_file="transit_performance_detailed.csv"):
    print(f"\nGenerating detailed CSV: {output_file}...")
    
    required_columns = [
        "tracking_number",
        "service_type",
        "carrier_code",
        "package_weight_kg",
        "packaging_type",
        "origin_city",
        "origin_state",
        "origin_pincode",
        "destination_city",
        "destination_state",
        "destination_pincode",
        "pickup_datetime_ist",
        "delivery_datetime_ist",
        "total_transit_hours",
        "num_facilities_visited",
        "num_in_transit_events",
        "time_in_inter_facility_transit_hours",
        "avg_hours_per_facility",
        "is_express_service",
        "delivery_location_type",
        "num_out_for_delivery_attempts",
        "first_attempt_delivery",
        "total_events_count"
    ]
    
    available_columns = [col for col in required_columns if col in df.columns]
    output_df = df[available_columns].copy()
    
    output_df.to_csv(output_file, index=False)
    print(f"✓ Detailed CSV saved: {output_file}")
    print(f"  Rows: {len(output_df)}, Columns: {len(output_df.columns)}")
    
    return output_df


def create_summary_csv(df, output_file="transit_performance_summary.csv"):
    print(f"\nGenerating summary CSV: {output_file}...")
    
    summary_rows = []
    
    total_shipments = len(df)
    summary_rows.append({
        "metric_category": "Overall Metrics",
        "metric_name": "total_shipments_analyzed",
        "metric_value": total_shipments
    })
    
    transit_hours = df["total_transit_hours"].dropna()
    if len(transit_hours) > 0:
        summary_rows.append({
            "metric_category": "Overall Metrics",
            "metric_name": "avg_transit_hours",
            "metric_value": transit_hours.mean()
        })
        summary_rows.append({
            "metric_category": "Overall Metrics",
            "metric_name": "median_transit_hours",
            "metric_value": transit_hours.median()
        })
        summary_rows.append({
            "metric_category": "Overall Metrics",
            "metric_name": "std_dev_transit_hours",
            "metric_value": transit_hours.std()
        })
        summary_rows.append({
            "metric_category": "Overall Metrics",
            "metric_name": "min_transit_hours",
            "metric_value": transit_hours.min()
        })
        summary_rows.append({
            "metric_category": "Overall Metrics",
            "metric_name": "max_transit_hours",
            "metric_value": transit_hours.max()
        })
    
    facilities = df["num_facilities_visited"].dropna()
    if len(facilities) > 0:
        summary_rows.append({
            "metric_category": "Facility Metrics",
            "metric_name": "avg_facilities_per_shipment",
            "metric_value": facilities.mean()
        })
        summary_rows.append({
            "metric_category": "Facility Metrics",
            "metric_name": "median_facilities_per_shipment",
            "metric_value": facilities.median()
        })
        
        mode_values = facilities.mode()
        summary_rows.append({
            "metric_category": "Facility Metrics",
            "metric_name": "mode_facilities_per_shipment",
            "metric_value": mode_values.iloc[0] if len(mode_values) > 0 else None
        })
    
    avg_hours_facility = df["avg_hours_per_facility"].dropna()
    if len(avg_hours_facility) > 0:
        summary_rows.append({
            "metric_category": "Facility Metrics",
            "metric_name": "avg_hours_per_facility",
            "metric_value": avg_hours_facility.mean()
        })
        summary_rows.append({
            "metric_category": "Facility Metrics",
            "metric_name": "median_hours_per_facility",
            "metric_value": avg_hours_facility.median()
        })
    
    service_types = df["service_type"].dropna().unique()
    for service_type in service_types:
        service_data = df[df["service_type"] == service_type]
        
        service_transit = service_data["total_transit_hours"].dropna()
        if len(service_transit) > 0:
            summary_rows.append({
                "metric_category": "Service Type Comparison",
                "metric_name": f"avg_transit_hours_by_service_type_{service_type}",
                "metric_value": service_transit.mean()
            })
        
        service_facilities = service_data["num_facilities_visited"].dropna()
        if len(service_facilities) > 0:
            summary_rows.append({
                "metric_category": "Service Type Comparison",
                "metric_name": f"avg_facilities_by_service_type_{service_type}",
                "metric_value": service_facilities.mean()
            })
        
        summary_rows.append({
            "metric_category": "Service Type Comparison",
            "metric_name": f"count_shipments_by_service_type_{service_type}",
            "metric_value": len(service_data)
        })
    
    first_attempt = df["first_attempt_delivery"].dropna()
    if len(first_attempt) > 0:
        percentage_first_attempt = (first_attempt.sum() / len(first_attempt)) * 100
        summary_rows.append({
            "metric_category": "Delivery Performance",
            "metric_name": "pct_first_attempt_delivery",
            "metric_value": percentage_first_attempt
        })
    
    ofd_attempts = df["num_out_for_delivery_attempts"].dropna()
    if len(ofd_attempts) > 0:
        summary_rows.append({
            "metric_category": "Delivery Performance",
            "metric_name": "avg_out_for_delivery_attempts",
            "metric_value": ofd_attempts.mean()
        })
    
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(output_file, index=False)
    print(f"✓ Summary CSV saved: {output_file}")
    print(f"  Metrics: {len(summary_df)}")
    
    return summary_df


def main():
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        possible_files = [
            "swift_assignment_data.json",
            "Swift Assignment 4 - Dataset (2).json",
            "dataset.json",
            "data.json"
        ]
        json_file = None
        for filename in possible_files:
            if os.path.exists(filename):
                json_file = filename
                break
        
        if not json_file:
            json_file = "swift_assignment_data.json"
    
    try:
        print("=" * 60)
        print("SWIFT Assignment - Transit Performance Analysis")
        print("=" * 60)
        
        df = load_data(json_file)
        
        print(f"\nData Exploration:")
        print(f"  Total shipments processed: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        print(f"\nFirst few rows:")
        print(df.head())
        
        create_detailed_csv(df)
        create_summary_csv(df)
        
        print("\n" + "=" * 60)
        print("Analysis Complete!")
        print("=" * 60)
        print(f"\nOutput files generated:")
        print(f"  1. transit_performance_detailed.csv")
        print(f"  2. transit_performance_summary.csv")
        
    except FileNotFoundError:
        print(f"\nError: File '{json_file}' not found.")
        print("Please ensure the JSON file is in the current directory.")
    except Exception as e:
        print(f"\nError during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
