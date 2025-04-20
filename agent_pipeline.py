# agent_pipeline.py

import streamlit as st
import os

from langchain_openai import AzureChatOpenAI
import json

import io
import base64
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredCSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langgraph.graph import StateGraph,START, END
from typing_extensions import TypedDict
from pprint import pprint
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import glob

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Azure OpenAI config
GPT_DEPLOYMENT_NAME = "gpt-4o"
os.environ["AZURE_OPENAI_API_KEY"] = "Give your Azure openai "
os.environ["AZURE_OPENAI_ENDPOINT"] = "Give your endpoint"
os.environ["OPENAI_API_VERSION"] = "Give your api version"

llm = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    openai_api_version="Give your api version",
    azure_deployment=GPT_DEPLOYMENT_NAME,
)


class RetrieverAgent:
    def __init__(self, llm):
        self.llm = llm
        self.prompt_template = ChatPromptTemplate.from_messages([
            SystemMessage(
                content= """You are a highly skilled financial research analyst with deep expertise in both fundamental and technical investing.
                            You analyze financial reports, charts, and commentary with a blended approach inspired by:

                            - **Peter Lynch & Warren Buffett** (business quality, earnings growth, moats, value)
                            - **Mark Minervini** (Volatility Contraction Pattern, price/volume analysis)
                            - **Darvas Box Theory** (price consolidation and breakout zones)

                            You interpret news and visuals with precision and convert them into:
                            - **Investor-grade stock evaluations**
                            - **Sentiment signals (Bullish / Bearish / Neutral)**
                            - **Actionable market insights**

                            Always be analytical, structured, and insightful. Your job is to turn raw financial data into clear investment intelligence."""
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])

    def retrieve_document_chunks(self, state):
        file_path = state["question"]
        output_dir = "temp_images"
        os.makedirs(output_dir, exist_ok=True)

        # Convert PDF to images
        images = convert_from_path(file_path)
        image_summaries = []

        for i, img in enumerate(images):
            image_path = os.path.join(output_dir, f"page_{i+1}.png")
            img.save(image_path, "PNG")

            # Convert image to base64
            img_path = Path(image_path)
            img_base64 = base64.b64encode(img_path.read_bytes()).decode("utf-8")

            # Send base64 image to LLM
            messages = [
                HumanMessage(
                    content=[
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}",
                            },
                        },
                        {
                            "type": "text",
                            "text": """You are a financial analysis expert with OCR-level precision. Your task is to extract and organize **all useful financial and market data** from this image.
                            Be thorough. Extract everything — even small notes — and organize the output into the following sections:
                            1. **Headlines & Subtitles**: Market headlines, themes, article titles.
                            2. **Tickers & Company Names**: All stock names, abbreviations, and tickers.
                            3. ** Table**: If any table data is present please analysis that data and understand that data .
                            4. **Numerical Data**: Price targets, EPS, P/E ratios, earnings surprises, volume spikes, % changes, etc.
                            5. **Visual Chart Interpretations**: Describe visible price action patterns, trend directions, chart shapes, arrows, or technical annotations.
                            6. **Recommendations**: Mentions of Buy / Sell / Hold ratings, upgrades, or analyst outlooks.
                            7. **Sector Mentions**: Note any specific industries, sectors, or themes (e.g., "AI", "energy", "small caps").
                            8. **Dates & Timeframes**: Reference any earnings dates, YTD references, or outlook periods.
                            9. **Commentary / Quotes**: Pull analyst or author comments that may imply sentiment or conviction.

                            💡 Present the result as a **structured bullet-point list** under the above headings."""

                        },
                    ]
                )
            ]

            response = self.llm.invoke(messages)
            # print(response.content)
            image_summaries.append(response.content)

        # Final summary from all image summaries
        combined_summary_prompt = (
                    """You are a senior financial strategist. Based on the extracted summaries from each page of a stock market insights document, create a **comprehensive and structured market report**.
                    Structure the output as follows:

                    1. **Executive Summary**:
                    - High-level overview of the document.
                    - Market themes, sentiment tone, standout opportunities or risks.

                    2. **Key Stock Mentions**:
                    - List all tickers or companies discussed.
                    - For each, summarize what was said and any implied stance (Bullish/Bearish/Neutral).

                    3. **Fundamental Analysis (Lynch & Buffett Style)**:
                    - Assess business model quality, growth, earnings power, and valuation.
                    - Highlight any economic moats or quality of management.

                    4. **Technical Analysis (Minervini & Darvas Inspired)**:
                    - Note any breakout setups, consolidation zones, VCP patterns, volume contraction, or Darvas Boxes.
                    - Describe actionable technical signals if present.

                    5. **Sentiment Overview**:
                    - Classify tone: Bullish / Bearish / Neutral.
                    - Back this up with commentary, word choice, and analyst outlooks.

                    6. **Market Implications**:
                    - Suggest sectors or trends worth tracking.
                    - Mention investor actions implied (watchlist, entry/exit zone, etc.).

                    7. **Top 2–3 Stock Picks (Optional)**:
                    - Highlight the most actionable, high-conviction names with rationale.

                    🎯 Write it like a professional market insights report — clear, actionable, and precise."""

                                        + "\n\n".join(image_summaries)
                    )
        messages = [HumanMessage(content=combined_summary_prompt)]
        final_summary = (self.prompt_template | self.llm).invoke(messages)

        for img_file in glob.glob(os.path.join(output_dir, "*.png")):
            os.remove(img_file)

        return {"final_summary": final_summary.content}

# Define input/output state for LangChain
class SummaryState(TypedDict):
    question: str
    final_summary: str

# Create retriever agent
retriever_agent = RetrieverAgent(llm)

# Build LangChain workflow
workflow = StateGraph(SummaryState)
workflow.add_node("RetrieverAgent", retriever_agent.retrieve_document_chunks)
workflow.add_edge(START, "RetrieverAgent")
workflow.add_edge("RetrieverAgent", END)
app = workflow.compile()
