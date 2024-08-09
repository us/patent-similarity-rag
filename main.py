import os
from langchain.prompts import PromptTemplate
from langchain.output_parsers.list import NumberedListOutputParser
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_community.chat_models import ChatOpenAI
import serpapi

model_name = 'gpt-4-0125-preview'

openai_key = os.getenv("OPENAI_API_KEY")
serpapi_key = os.getenv("SERPAPI_KEY")
# generate search terms using OpenAI
def generate_search_terms(input_text: str, number_of_generated_search_terms):
    llm = ChatOpenAI(model_name=model_name, temperature=0.0)
    output_parser = NumberedListOutputParser()
    format_instructions = output_parser.get_format_instructions()
    prompt = PromptTemplate(
        template="As a search specialist with expertise in optimizing searches in the Google Patents database, your task is to generate " + str(number_of_generated_search_terms) + " optimal keyword or keyword list like single and multiple keywords(please choose correct terms, i want to get at least 10 results for each query, don't be too specific) like, `(rabbit toy), (coffee brew) AND (pot) OR (top), (stabilization system), (vr heading) OR (logic freq)`, so dont use \" or ' use only phranthesis,  searches to find similar patents for the following invention idea: ---BEGINNING--- `{user_input}` ---END--- {format_instructions}\n",
        input_variables=["user_input"],
        partial_variables={"format_instructions": format_instructions}
    )

    output = llm.predict(text=prompt.format(user_input=input_text))
    output_list = output_parser.parse(output)
    return output_list

# search Google Patents using SerpApi
def search_on_google_patents(terms: list):
    # multiple_queries = ';'.join(terms)
    search_terms_patterns ={}
    for search_term in terms:
        params = {
            "engine": "google_patents",
            "q": search_term,
            "clustered": "true",
            "scholar": "true",
            "api_key": serpapi_key
        }
        results = serpapi.search(params)
        if results.get('error', False):
            raise results['error']
        organic_results = results["organic_results"]

        patents = []
        for result in organic_results:
            if "patent_id" in result:
                patent = {
                    "patentTitle": result["title"],
                    "patentNumber": result["publication_number"],
                    "inventors": [result["inventor"]],
                    "assignee": result["assignee"],
                    "abstract": result["snippet"],
                    "publicationDate": result["publication_date"],
                    "filingDate": result["filing_date"],
                    "patentUrl": result["serpapi_link"]
                }
                patents.append(patent)
        search_terms_patterns[search_term] = patents
    return search_terms_patterns

# check similarity of patents using OpenAI
def check_similarity_of_patents(input_text, patents: list):
    llm = ChatOpenAI(model_name=model_name, temperature=0.0)
    
    response_schemas = [
        ResponseSchema(
            name="listOfPatents",
            description="List of dicts of patentTitle, patentNumber and similarityScore (score over 100): [{patentTitle: string, patentNumber: string, similarityScore: number}]",
            type="array(objects)"
            )
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    prompt = PromptTemplate(
        template="Could you please generate a semantic similarity score out of 100 for the following patent information {user_input}, comparing it with the following abstracts:" + '\n'.join([f"\n===BEGINNING=== {i+1} - {patent['patentTitle']} - {patent['patentNumber']} - {patent['abstract']} ===END===" for i, patent in enumerate(patents)]) + "\n{format_instructions}\n",
        input_variables=["user_input"],
        partial_variables={"format_instructions": format_instructions}
    )
    output = llm.predict(text=prompt.format(user_input=input_text))
    output_list = output_parser.parse(output)
    return output_list

# merge patents with similarity data
def merge_patents_with_similarity(patents, similarity_data):
    merged_list = []
    for patent in patents:
        patent_number = patent['patentNumber']
        for similarity_patent in similarity_data['listOfPatents']:
            if similarity_patent['patentNumber'] == patent_number:
                patent['similarityScore'] = similarity_patent['similarityScore']
                patent['patentGoogleUrl'] = f"https://patents.google.com/patent/{patent_number}"
                break
        merged_list.append(patent)
    merged_list = sorted(merged_list, key=lambda x: x['similarityScore'], reverse=True)
    return list(merged_list)

# sort patents by similarity score
def sort_patents_by_similarity_score(data):
    sorted_patents = sorted(data, key=lambda x: x['similarityScore'], reverse=True)
    return sorted_patents
