import streamlit as st
from main import *

# Streamlit app starts here
st.title("Patent Similarity Search App (LLM + RAG + GOOGLE PATENTS)")

st.subheader("User Input")
user_input = st.text_area("Enter Patent Data", "Paste your patent details here...")
# Sidebar for user input
with st.sidebar:
    number_of_generated_search_terms = st.number_input("Number of Search Terms to Generate", value=5)
    top_k_patterns = st.number_input("Top K Patterns to Search", value=10)
    model_name = st.text_input("OpenAI Model Name", "gpt-4-0125-preview")
    openai_key = st.text_input("OpenAI API Key", '')
    serpapi_key = st.text_input("SerpAPI API Key", '')

    # Update environment variables if there are changes
    if openai_key != os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = openai_key

    if serpapi_key != os.getenv("SERPAPI_KEY"):
        os.environ["SERPAPI_KEY"] = serpapi_key

# Main content
if st.button("Find Similar Patents"):
    try:
        with st.spinner('Generating search terms...'):
            generated_search_terms = generate_search_terms(user_input, number_of_generated_search_terms)
        st.success("Search terms generated!")
        st.write("Generated search terms: ", generated_search_terms)
        
        with st.spinner('Searching for patents...'):
            search_terms_patterns = search_on_google_patents(generated_search_terms)
        st.success("Patents search completed!")
        # st.write("Patents found: ", patents_list)
        st.subheader("Top Patents Found for Search Terms")
        for search_term, patents in search_terms_patterns.items():
            st.write(f"Top {top_k_patterns} patents found for search term: {search_term}")
            if len(patents) == 0:
                st.write(f"No patents found for search term: {search_term}")
                continue
            else:
                patent_titles = [patent['patentTitle'] for patent in patents]
                st.json(patent_titles[:top_k_patterns])
        
        patents_list = []
        with st.spinner('Checking similarities of patents...'):
            # get patents from all search terms
            for search_term, patents in search_terms_patterns.items():
                patents_list.extend(patents[:top_k_patterns])
            similarities = check_similarity_of_patents(user_input, patents_list)
        st.success("Similarity check completed!")
        # st.write("Similarities found: ", similarities)
        
        for patent in similarities['listOfPatents']:
            for p in patents_list:
                if patent['patentNumber'] == p['patentNumber']:
                    p['similarityScore'] = patent['similarityScore']
                    p['patentGoogleUrl'] = f"https://patents.google.com/patent/{p['patentNumber']}"
                    break
        patents_list = list(sorted(patents_list, key=lambda x: x['similarityScore'], reverse=True))
        # Displaying results
        st.subheader("Top Similar Patents")
        st.json(patents_list)
    except Exception as e:
        st.error(f"An error occurred: {e}")
