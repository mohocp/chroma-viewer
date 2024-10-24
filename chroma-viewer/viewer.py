import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import streamlit as st

# Set the page layout to wide
st.set_page_config(layout="wide")

pd.set_option('display.max_columns', 4)

def main():
    st.title("ChromaDB Collections Viewer")

    # Initialize session state variables
    if 'host' not in st.session_state:
        st.session_state.host = 'localhost'
    if 'port' not in st.session_state:
        st.session_state.port = 8000
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False

    # Input fields for host and port
    host = st.text_input("Enter the Chroma server host:", value=st.session_state.host)
    port = st.number_input("Enter the Chroma server port:", min_value=1, max_value=65535, value=st.session_state.port, step=1)

    # Update session state with host and port
    st.session_state.host = host
    st.session_state.port = port

    # Connect to Chroma Server
    if not st.session_state.connected:
        if st.button("Connect to Chroma Server"):
            try:
                client = chromadb.HttpClient(host=host, port=int(port))
                st.session_state.client = client
                st.session_state.connected = True
                st.success("Connected to Chroma Server")
            except Exception as e:
                st.error(f"An error occurred: {e}")
                return

    # If connected, proceed to display collections
    if st.session_state.connected:
        client = st.session_state.client
        try:
            # Fetch the list of collections
            collections = client.list_collections()
            if not collections:
                st.info("No collections found on the server.")
                return

            st.header("Collections")

            # Add a button to delete all collections
            if st.button("Delete All Collections"):
                try:
                    for collection in collections:
                        client.delete_collection(collection.name)
                    st.success("All collections deleted.")
                    # Refresh the list of collections
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting all collections: {e}")
                return  # Exit after deleting all collections

            # Display each collection
            for collection in collections:
                # Display collection name with a delete button
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.subheader(f"Collection: **{collection.name}**")
                with col2:
                    if st.button("Delete Collection", key=f"delete_collection_{collection.name}"):
                        try:
                            client.delete_collection(collection.name)
                            st.success(f"Collection {collection.name} deleted.")
                            # Refresh the list of collections
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting collection {collection.name}: {e}")
                        return  # Exit after deleting the collection

                data = collection.get()

                if not data['ids']:
                    st.info("This collection is empty.")
                    continue

                # Build a dataframe
                df = pd.DataFrame({
                    'ID': data['ids'],
                    'Document': data.get('documents', [''] * len(data['ids'])),
                    'Metadata': data.get('metadatas', [{}] * len(data['ids'])),
                })

                # Display the dataframe as a table with delete buttons
                st.markdown("#### Items in the Collection")

                # Add table headers
                header_cols = st.columns([2, 5, 3, 1])
                header_cols[0].write("**ID**")
                header_cols[1].write("**Document**")
                header_cols[2].write("**Metadata**")
                header_cols[3].write("**Action**")

                # Display each item in the collection
                for index, row in df.iterrows():
                    cols = st.columns([2, 5, 3, 1])
                    with cols[0]:
                        st.write(row['ID'])
                    with cols[1]:
                        st.write(row['Document'])
                    with cols[2]:
                        st.write(row['Metadata'])
                    with cols[3]:
                        if st.button("Delete", key=f"delete_item_{collection.name}_{row['ID']}"):
                            try:
                                # Use collection.delete() to delete the item
                                collection.delete(ids=[row['ID']])
                                st.success(f"Item {row['ID']} deleted.")
                                # Refresh the data for the collection
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting item {row['ID']}: {e}")
                            return  # Exit after deleting the item
                st.markdown("---")

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
