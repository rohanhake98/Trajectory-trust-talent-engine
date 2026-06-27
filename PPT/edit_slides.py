import os
import re
import defusedxml.minidom as minidom

def create_run(doc, text, bold=False, typeface="Manrope SemiBold", size="1365"):
    r = doc.createElement("a:r")
    rPr = doc.createElement("a:rPr")
    rPr.setAttribute("lang", "en-GB")
    rPr.setAttribute("sz", size)
    if bold:
        rPr.setAttribute("b", "1")
    
    solidFill = doc.createElement("a:solidFill")
    srgbClr = doc.createElement("a:srgbClr")
    srgbClr.setAttribute("val", "202729")
    solidFill.appendChild(srgbClr)
    rPr.appendChild(solidFill)
    
    for tag in ["a:latin", "a:ea", "a:cs", "a:sym"]:
        el = doc.createElement(tag)
        el.setAttribute("typeface", typeface)
        rPr.appendChild(el)
        
    r.appendChild(rPr)
    
    t = doc.createElement("a:t")
    if text.startswith(" ") or text.endswith(" "):
        t.setAttribute("xml:space", "preserve")
    t.appendChild(doc.createTextNode(text))
    r.appendChild(t)
    return r

def split_bullet_text(bullet_text):
    # Splits "Keyword: Text" into ("Keyword:", " Text") or ("Whole Text", "")
    match = re.match(r"^([^:]+:\s*)(.*)$", bullet_text)
    if match:
        return match.group(1), match.group(2)
    return bullet_text, ""

def process_slide(slide_path, bullets, text_box_name=None, text_box_id=None):
    print(f"Processing slide: {os.path.basename(slide_path)}")
    with open(slide_path, "r", encoding="utf-8") as f:
        xml_content = f.read()
    
    doc = minidom.parseString(xml_content)
    
    # Find the shape tree
    spTree = doc.getElementsByTagName("p:spTree")[0]
    
    # Locate the target shape
    target_sp = None
    shapes = doc.getElementsByTagName("p:sp")
    
    for sp in shapes:
        cNvPrs = sp.getElementsByTagName("p:cNvPr")
        if cNvPrs:
            cNvPr = cNvPrs[0]
            name = cNvPr.getAttribute("name")
            id_val = cNvPr.getAttribute("id")
            if text_box_name and text_box_name in name:
                target_sp = sp
                break
            if text_box_id and id_val == text_box_id:
                target_sp = sp
                break
                
    if not target_sp:
        raise ValueError(f"Could not find shape with name '{text_box_name}' or id '{text_box_id}' in {slide_path}")
        
    txBody = target_sp.getElementsByTagName("p:txBody")[0]
    
    # Extract the original a:pPr (bullet/paragraph properties) to copy
    orig_p = txBody.getElementsByTagName("a:p")[0]
    orig_pPr = orig_p.getElementsByTagName("a:pPr")[0].cloneNode(True)
    
    # Remove all existing a:p elements
    for p in list(txBody.getElementsByTagName("a:p")):
        txBody.removeChild(p)
        
    # Rebuild paragraphs
    for b in bullets:
        p = doc.createElement("a:p")
        p.appendChild(orig_pPr.cloneNode(True))
        
        # Split into keyword and normal text for bolding
        keyword, normal_text = split_bullet_text(b)
        if normal_text:
            p.appendChild(create_run(doc, keyword, bold=True))
            p.appendChild(create_run(doc, normal_text, bold=False))
        else:
            p.appendChild(create_run(doc, keyword, bold=False))
            
        txBody.appendChild(p)
        
    # Write back XML
    with open(slide_path, "w", encoding="utf-8") as f:
        doc.writexml(f, encoding="utf-8")

def process_slide1(slide_path):
    print("Processing Slide 1 (Cover)")
    with open(slide_path, "r", encoding="utf-8") as f:
        xml_content = f.read()
        
    doc = minidom.parseString(xml_content)
    
    # We want to replace:
    # 1. "Team Name :" with "Team Name: Trajectory-trust-talent-engine"
    # 2. "Team Leader Name :" with "Team Leader: Rohan Hake (ML Engineer, rohanhake98@gmail.com)"
    # 3. "Problem Statement :" with "Problem Statement: Replace flat keyword matching with career velocity forecasting. Redrob AI Hiring Challenge, June 25, 2026."
    
    shapes = doc.getElementsByTagName("p:sp")
    for sp in shapes:
        txBody_list = sp.getElementsByTagName("p:txBody")
        if not txBody_list:
            continue
        txBody = txBody_list[0]
        ts = txBody.getElementsByTagName("a:t")
        for t in ts:
            text = t.firstChild.nodeValue
            if "Team Name :" in text:
                t.firstChild.nodeValue = "Team Name: Trajectory-trust-talent-engine"
            elif "Team Leader Name :" in text:
                t.firstChild.nodeValue = "Team Leader: Rohan Hake (ML Engineer, rohanhake98@gmail.com)"
            elif "Problem Statement :" in text:
                t.firstChild.nodeValue = "Problem Statement: Replace flat keyword matching with career velocity forecasting. Redrob AI Hiring Challenge, June 25, 2026."
                
    with open(slide_path, "w", encoding="utf-8") as f:
        doc.writexml(f, encoding="utf-8")

def setup_slide7(slide7_path, slide6_path, bullets):
    print("Setting up Slide 7 (Architecture)")
    # Slide 7 does not have a content shape box. We will clone shape 92 from slide 6, insert it into slide 7,
    # rename it to unique id, and populate it with Slide 7 bullets.
    with open(slide6_path, "r", encoding="utf-8") as f:
        xml6 = f.read()
    with open(slide7_path, "r", encoding="utf-8") as f:
        xml7 = f.read()
        
    doc6 = minidom.parseString(xml6)
    doc7 = minidom.parseString(xml7)
    
    # Find shape 92 in slide 6
    target_sp = None
    for sp in doc6.getElementsByTagName("p:sp"):
        cNvPrs = sp.getElementsByTagName("p:cNvPr")
        if cNvPrs and cNvPrs[0].getAttribute("id") == "92":
            target_sp = sp
            break
            
    if not target_sp:
        raise ValueError("Could not find shape 92 in slide 6")
        
    # Clone shape 92 to doc7
    cloned_sp = doc7.importNode(target_sp, deep=True)
    
    # Update ID and Name of cloned shape in slide 7
    cNvPr = cloned_sp.getElementsByTagName("p:cNvPr")[0]
    cNvPr.setAttribute("id", "99")
    cNvPr.setAttribute("name", "Google Shape;99;p19")
    
    # Add cloned shape to slide 7 spTree
    spTree = doc7.getElementsByTagName("p:spTree")[0]
    spTree.appendChild(cloned_sp)
    
    # Save slide 7 XML
    with open(slide7_path, "w", encoding="utf-8") as f:
        doc7.writexml(f, encoding="utf-8")
        
    # Now run standard processing on slide 7 using shape 99
    process_slide(slide7_path, bullets, text_box_id="99")

# Content configuration
slides_content = {
    2: [
        "Problem: Flat resume keyword matching filters out high-velocity talent and rewards keyword-stuffing.",
        "Objective: Rank candidates by career velocity and behavioral convertibility via a Trust Shield.",
        "Innovation: Shifting from static text matching to counterfactual career velocity forecasting.",
        "Features: NetworkX transition path analysis, skill stuffing gates, and recruiter interaction signals.",
        "Business Value: Decreases screening cycles by 70% and eliminates fake resumes.",
        "Workflow: [JSONL Pool] ➔ [Normalize & Clean] ➔ [Trust & Velocity Scoring] ➔ [Top 100 CSV]."
    ],
    3: [
        "JD Ingestion: Parses raw job descriptions to extract target title and target experience.",
        "Skill Extraction: Classifies must-have and nice-to-have skills into a target dictionary.",
        "Candidate Analysis: Extracts tenure, career velocity slope, and industry transition relevance.",
        "Semantic Matching: Replaces simple keyword matching with TF-IDF title similarity and transition graph proximity.",
        "Incomplete Profiles: Resolves missing end-dates to current reference date and averages numeric features.",
        "Extraction Flow: [Raw JD] ➔ [Regex Normalizer] ➔ [Canonical Title & Skills Dictionary]."
    ],
    4: [
        "Retrieval & Pipeline: Streams candidate JSONL profiles through vectorized NumPy similarity calculations.",
        "Embedding Model: Computes Cosine similarity over TF-IDF vectors of candidate vs. target titles.",
        "Weight Distribution: Blends Static Fit (25%), Trajectory (40%), and Behavioral Convertibility (35%) scores.",
        "Formula Box: Score = Trust × (0.25·Static + 0.40·Trajectory + 0.35·Convertibility)",
        "Ranking Flowchart: [Static/Trajectory/Convertibility] ➔ [Composite Score] ──(× Trust)──➔ [Deterministic Sorted Rank]",
        "Deterministic Tie-Breaking: Sorts descending by final score; breaks ties alphabetically by candidate ID."
    ],
    5: [
        "Card 1: Explainability: Generates automated, template-based sentence justifications from database fields.",
        "Card 2: Hallucination Prevention: Bypasses open-ended LLM text generation to ensure 100% factual accuracy.",
        "Card 3: Trust Shield: Detects fake profiles by flagging overlapping dates and skill-stuffing.",
        "Card 4: Validation Gate: Validates inputs using Pydantic, logging malformed profiles without pipeline failure.",
        "Missing Data: Defaults missing end-dates to reference date and averages unspecified values."
    ],
    6: [
        "Horizontal Pipeline: Input ➔ Preprocessing ➔ JD Analysis ➔ Candidate Analysis ➔ Embedding ➔ Scoring ➔ Ranking ➔ Output",
        "Stream Processing: Streams candidate JSONL profiles through normalization, scoring, and trust-shield gates.",
        "Performance: Generates 100 final candidate ranks with grounded justifications in under 3 minutes."
    ],
    7: [
        "Architecture: User ➔ Frontend (Vanilla JS) ➔ Backend (FastAPI) ➔ Embedding Model (Scikit-Learn TF-IDF) ➔ Ranking Engine (Vectorized NumPy) ➔ Database (Streaming JSONL) ➔ Output (CSV)",
        "System: Scalable, database-free architecture designed for local reproduction with zero API dependencies."
    ],
    8: [
        "KPIs: Candidates Processed: 100,000 | Runtime: <3 min | Accuracy: 100% tests passed | Memory: <500MB",
        "Comparison: Method: Keyword Match vs. Our Engine. Time: >2h vs. <3m. Trust: No vs. Yes.",
        "Sample Output: Rank 1: CAND_0002025 (Score: 0.7847). Rank 2: CAND_0071974 (Score: 0.7657).",
        "Conclusion: The engine processes 100K profiles rapidly, surfacing talent while blocking honeypots."
    ],
    9: [
        "Programming: Python 3.13 (Core runtime)",
        "ML / NLP: Scikit-Learn (TF-IDF similarity, no GPU overhead)",
        "Backend / Frontend: FastAPI (Asynchronous API) / HTML5 & Vanilla JS (Zero-dependency UI)",
        "Database / Vis: JSONL (In-memory generator streaming) / Chart.js (Interactive UI visualization)",
        "VC / Deployment: Git & GitHub (Code collaboration) / Local Uvicorn server"
    ],
    10: [
        "GitHub & PDF: github.com/rohanhake98/Trajectory-trust-talent-engine (walkthrough.md)",
        "CSV & Dataset: output/submission.csv | Redrob AI Challenge (100K profiles)",
        "Commands: pip install -r requirements.txt && python rank.py",
        "Contact: rohanhake98@gmail.com | QR Code Placeholder"
    ]
}

# Mapping of slide numbers to their text box IDs or unique name elements
slide_box_mappings = {
    2: {"text_box_id": "64"},
    3: {"text_box_id": "71"},
    4: {"text_box_id": "78"},
    5: {"text_box_id": "85"},
    6: {"text_box_id": "92"},
    8: {"text_box_id": "105"},
    9: {"text_box_id": "112"},
    10: {"text_box_id": "119"}
}

unpacked_dir = "/app/PPT/unpacked/ppt/slides"

def main():
    # Process Slide 1
    process_slide1(os.path.join(unpacked_dir, "slide1.xml"))
    
    # Process Slide 2 to 6, 8 to 10
    for num, mapping in slide_box_mappings.items():
        slide_file = os.path.join(unpacked_dir, f"slide{num}.xml")
        bullets = slides_content[num]
        process_slide(slide_file, bullets, text_box_id=mapping["text_box_id"])
        
    # Process Slide 7
    setup_slide7(
        os.path.join(unpacked_dir, "slide7.xml"),
        os.path.join(unpacked_dir, "slide6.xml"),
        slides_content[7]
    )
    
    print("All slides processed successfully!")

if __name__ == "__main__":
    main()
