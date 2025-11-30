# Courier Transit Performance Analysis

This project analyzes how shipments move through a courier network. Think of it like analyzing Uber trips - we track where packages go, how long they take, and how efficiently they're delivered.

## What This Does

Imagine you're a courier company manager. You want to know:
- How fast are we delivering packages?
- How many warehouses do packages visit?
- Are we delivering on the first try?
- Which routes are most efficient?

This tool answers all those questions by analyzing shipment tracking data.

---

## Quick Start

### 1. Install Required Packages

```bash
pip install -r requirements.txt
```

### 2. Run the Analysis

Place your JSON data file in this folder, then run:

```bash
python transit_performance_analysis.py "Swift Assignment 4 - Dataset (2).json"
```

Or if your file is named `swift_assignment_data.json`:

```bash
python transit_performance_analysis.py
```

### 3. Check the Results

You'll get two CSV files:
- **transit_performance_detailed.csv** - Details for each shipment
- **transit_performance_summary.csv** - Overall statistics

Open them in Excel or Google Sheets to explore!

---

## What You Get

### Detailed Report (transit_performance_detailed.csv)

One row for each shipment showing:
- Where it started and ended
- How long it took to deliver
- How many facilities it visited
- Whether it was delivered on first attempt
- And much more!

**Example:**
```
Tracking: 391128701026
Route: Bangalore → Gurgaon
Time: 94 hours (4 days)
Facilities: 4
First Attempt: Yes ✅
```

### Summary Statistics (transit_performance_summary.csv)

Overall network performance:
- Average delivery time: **94 hours**
- Average facilities per shipment: **4.2**
- First attempt success rate: **64%**

---

## Real Results from Sample Data

After processing 99 shipments, here's what we found:

📊 **Delivery Performance:**
- Average transit time: 94 hours (about 4 days)
- Fastest delivery: 15 hours
- Slowest delivery: 544 hours (had issues)

🏭 **Network Efficiency:**
- Most shipments visit 4 different facilities
- Each facility adds about 22 hours on average

✅ **Success Rate:**
- 64% delivered on first attempt
- 36% needed multiple attempts

---

## How It Works (Simple Explanation)

1. **Read the Data:** Loads shipment tracking information from JSON file
2. **Extract Info:** Pulls out important details like locations, timestamps, events
3. **Calculate Metrics:** Figures out transit times, facility counts, success rates
4. **Generate Reports:** Creates easy-to-read CSV files with all results

---

## Input Data Format

The script expects a JSON file with shipment tracking data. Each shipment should have:
- Tracking number
- Origin and destination addresses
- Package details (weight, type)
- Event history (pickup, transit, delivery events)

The script automatically handles:
- ✅ Missing information
- ✅ Different date formats
- ✅ Incomplete data
- ✅ Various data structures

---

## Output Files Explained

### transit_performance_detailed.csv

Contains 23 columns with information about each shipment:
- Basic info (tracking number, service type, carrier)
- Package details (weight, packaging)
- Origin and destination addresses
- Pickup and delivery timestamps
- Performance metrics (transit time, facilities visited, etc.)

### transit_performance_summary.csv

Contains aggregated statistics in 4 categories:
1. **Overall Metrics** - Transit time statistics
2. **Facility Metrics** - Facility visit statistics
3. **Service Type Comparison** - Performance by service type
4. **Delivery Performance** - Delivery attempt statistics

---

## Features

✨ **Smart Data Handling**
- Works even when some data is missing
- Handles different timestamp formats
- Processes incomplete information gracefully

📈 **Comprehensive Analysis**
- Calculates all key performance metrics
- Identifies patterns in transit routes
- Measures delivery success rates

🔧 **Production Ready**
- Error handling for real-world data issues
- Clean, maintainable code
- Easy to extend with new features

---

## Example Usage

```bash
# Process the dataset
python transit_performance_analysis.py "Swift Assignment 4 - Dataset (2).json"

# Output:
# ✓ Processed 99 shipments
# ✓ Generated transit_performance_detailed.csv
# ✓ Generated transit_performance_summary.csv
```

Then open the CSV files to see:
- Which shipments took longest
- Which routes are most efficient
- Overall network performance

---

## Understanding the Metrics

**Total Transit Hours:** Time from pickup to delivery

**Facilities Visited:** Number of unique warehouses/stations the package passed through

**First Attempt Delivery:** Whether the package was delivered successfully on the first delivery attempt

**Out-for-Delivery Attempts:** Number of times the delivery vehicle went out to deliver

**Express Service:** Whether the shipment used premium fast delivery service

---

## Troubleshooting

**File not found?**
- Make sure your JSON file is in the same folder as the script
- Check the file name matches what you're using

**Missing columns in output?**
- Check that your JSON file has the required tracking data structure
- The script will handle missing fields gracefully

**Need help?**
- Check `EXPLANATION.md` for detailed explanation
- Review the code comments in `transit_performance_analysis.py`

---

## What This Project Demonstrates

✅ Real-world data engineering skills
✅ Handling messy, real data
✅ Calculating business metrics
✅ Creating actionable reports
✅ Production-quality code

Perfect for:
- Data engineering portfolios
- Learning data analysis
- Understanding logistics systems
- Building similar tools

---

## Files in This Project

- `transit_performance_analysis.py` - Main analysis script
- `requirements.txt` - Python package dependencies
- `EXPLANATION.md` - Detailed explanation in easy English
- `README.md` - This file
- Output files (generated when you run):
  - `transit_performance_detailed.csv`
  - `transit_performance_summary.csv`

---

*Built for analyzing courier logistics performance - making shipping data easy to understand!*
