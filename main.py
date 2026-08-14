from app.graph import graph


def main():

    user_query = (
        "Identify the top 3 states by total sales. Also, check the dataset for "
        "any data quality issues (like missing values) and explain how they might affect the analysis."
    )

    initial_state = {
        "input": user_query,

        "dataset_path": "data/nigeria_messy_sales_dataset.csv",

        "dataset_context": """
        File: nigeria_messy_sales_dataset.csv

        Columns:
        - Customer Name: Name of the customer
        - State: The Nigerian state where the sale occurred
        - Product: The item purchased
        - Units Sold: Number of units purchased
        - Unit Price: Price per unit
        - Total Sale: Total value of the sale
        - Sale Date: The date of the sale (DD-MM-YYYY)
        - Sales Channel: How the sale was made (Online, Retail, Wholesale, Direct)
        - Order ID: Unique identifier for the order
        """,

        "plan": [],

        "past_steps": [],

        "final_report": None
    }

    print("Starting Autonomous Data Analyst...\n")

    final_state = graph.invoke(
        initial_state,
        config={
            "recursion_limit": 50
        }
    )
    print("FINAL REPORT")


    print(final_state["final_report"])


if __name__ == "__main__":
    main()