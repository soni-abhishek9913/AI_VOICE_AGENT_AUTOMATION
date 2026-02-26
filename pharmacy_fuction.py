import csv
import os

CSV_FILE = "orders.csv"

ORDERS_DB = {"next_id": 1}

DRUG_DB = {
    "aspirin": {"name": "Acetylsalicylic Acid", "price": 5.99, "quantity": 30},
    "ibuprofen": {"name": "Ibuprofen", "price": 7.99, "quantity": 20},
    "acetaminophen": {"name": "Acetaminophen", "price": 6.99, "quantity": 25},
    "metformin": {"name": "Metformin Hydrochloride", "price": 12.50, "quantity": 60},
    "lisinopril": {"name": "Lisinopril", "price": 8.75, "quantity": 30},
    "atorvastatin": {"name": "Atorvastatin Calcium", "price": 15.25, "quantity": 30},
    "omeprazole": {"name": "Omeprazole", "price": 11.99, "quantity": 28}
}



def initialize_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["order_id", "customer", "drug", "quantity", "total", "status"])
        ORDERS_DB["next_id"] = 1
    else:
        with open(CSV_FILE, "r") as f:
            rows = list(csv.DictReader(f))
            if rows:
                ORDERS_DB["next_id"] = int(rows[-1]["order_id"]) + 1
            else:
                ORDERS_DB["next_id"] = 1


def get_drug_info(drug_name):
    drug = DRUG_DB.get(drug_name.lower())
    if not drug:
        return {"error": f"Drug '{drug_name}' not found"}
    return drug


def place_order(customer_name, drug_name):
    drug = DRUG_DB.get(drug_name.lower())
    if not drug:
        return {"error": f"Drug '{drug_name}' not found"}

    order_id = ORDERS_DB["next_id"]
    ORDERS_DB["next_id"] += 1

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            order_id,
            customer_name,
            drug["name"],
            drug["quantity"],
            drug["price"],
            "pending"
        ])

    return {
        "order_id": order_id,
        "message": f"Order {order_id} placed successfully",
        "total": drug["price"],
        "quantity": drug["quantity"]
    }


def lookup_order(order_id):
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["order_id"] == str(order_id):
                return row

    return {"error": f"Order {order_id} not found"}


FUNCTION_MAP = {
    "get_drug_info": get_drug_info,
    "place_order": place_order,
    "lookup_order": lookup_order
}