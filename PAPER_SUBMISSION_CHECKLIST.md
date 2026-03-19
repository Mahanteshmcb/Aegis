# Aegis Paper Submission Checklist (Day 2)

## 📋 Pre-Submission (30 minutes)

### Choose Your Target Venue
- [ ] Decide IEEE IoT Journal OR Sensors (MDPI) OR your college conference
- [ ] Visit conference website, write down:
  - [ ] Paper format requirements (page limit, margins, fonts)
  - [ ] Submission deadline
  - [ ] Conference contact email
  - [ ] Template link (LaTeX or Word)

### Download & Setup Template
- [ ] Download the template (LaTeX IEEEtran OR Word .docx)
- [ ] Create a new folder: `submission/`
- [ ] Copy template into `submission/`

---

## 📝 Content Reformatting (1–2 hours)

### Copy-Paste Content
- [ ] **Abstract** → template abstract section (trim to max 250 words)
- [ ] **Introduction** → template intro section
- [ ] **Related Work** → template related work section
- [ ] **Architecture** → template section 2
  - [ ] Paste high-level overview diagram (Mermaid ASCII)
  - [ ] Paste data flow diagram
  - [ ] Paste agent execution pipeline diagram
- [ ] **Implementation** → template section 3
  - [ ] Paste endpoint summary table
  - [ ] Paste code snippets (Python CRUD, Solidity contract)
- [ ] **Validation/Evaluation** → template section 4
  - [ ] Paste metrics table (availability, latency, throughput)
  - [ ] Paste comparison table (Azure vs GE vs IOTA vs Aegis)
- [ ] **Conclusion** → template conclusion section
- [ ] **Future Work** → if space allows, or as "Research Directions"
- [ ] **References** → template references section (all 10 citations)

### Adjust Formatting
- [ ] Check all figures/tables are numbered (Figure 1, 2, 3; Table 1, 2)
- [ ] Update all figure/table captions with descriptive text
- [ ] Check font sizes (must meet template specs: usually 10pt for body, 11pt for headings)
- [ ] Verify margins (usually 1 inch all sides for IEEE)
- [ ] Check page count (aim for 4–6 pages for extended abstract)

### Add Missing Sections
- [ ] Add "Author" or "About the Author" section:
  ```
  [Your Name] is a [student/researcher] in [Department] at [College/University]. 
  His interests include digital twins, edge computing, and autonomous systems.
  ```
- [ ] Add author email + affiliation to header/footer (if template requires)

---

## ✅ Final Review (30 minutes)

### Content Quality
- [ ] Read abstract aloud for clarity (no jargon overload)
- [ ] Verify all citations match reference list (no orphaned [#] numbers)
- [ ] Check all hyperlinks work (esp. [Online]. Available:)
- [ ] Verify section numbering is consistent (1. 2. 3. ... not 1 2 3)

### Grammar & Spelling
- [ ] Copy entire document into **Grammarly.com** (paste text)
  - First 10 suggestions are free; fix critical errors
- [ ] Search for common issues:
  - [ ] Double spaces (Ctrl+H, find "  ", replace " ")
  - [ ] Passive voice overuse (esp. "is used", "has been", etc.)
  - [ ] Undefined acronyms (first mention: spell out, then use acronym)

### Visual Check
- [ ] All diagrams are readable (not blurry or too small)
- [ ] All tables have borders and proper alignment
- [ ] No orphaned headings at page bottoms (add space or reflow)
- [ ] No overfull/underfull paragraphs (awkward line breaks)

### Technical Accuracy
- [ ] Code snippets compile/verify (copy `backend/crud.py` and `AegisAudit.sol` for accuracy)
- [ ] All metrics in validation section are realistic (matches prototype data)
- [ ] Related work comparison table is fair and complete

---

## 🚀 Submission (15 minutes)

### Export to PDF
- [ ] Save as PDF (File → Export/Print to PDF)
- [ ] Name: `AEGIS_IEEE_Extended_Abstract_[YourName]_2026.pdf`
- [ ] Check PDF opens correctly (no formatting corruption)
- [ ] **Page count:** Should be 4–6 pages

### Prepare Submission Packet
- [ ] Have ready:
  - [ ] PDF file
  - [ ] Your name + email
  - [ ] Affiliation (college/university)
  - [ ] Short bio (1–2 sentences)
  - [ ] Abstract (for web form, if applicable)
  - [ ] Keywords list (7 words, comma-separated)

### Submit to Conference
- [ ] Go to conference submission portal
- [ ] Create account (or login)
- [ ] Fill in author info:
  - [ ] Name, email, affiliation
  - [ ] Author role (Corresponding Author)
- [ ] Paste abstract into web form
- [ ] Paste keywords into web form
- [ ] Upload PDF
- [ ] Answer any custom questions (research area, funding, etc.)
- [ ] Review submission summary
- [ ] **Click SUBMIT**
- [ ] Save confirmation email/receipt number

### Backup & Cleanup
- [ ] Save confirmation screenshot
- [ ] Check email for submission confirmation (usually within 1 hour)
- [ ] Add paper to your CV / portfolio
- [ ] Archive submission files in `submissions/` folder

---

## 📊 Post-Submission

### Track Status
- [ ] Bookmark conference review system
- [ ] Check review status every 2–4 weeks
- [ ] Expected timeline: 8–12 weeks for IEEE, 3–4 weeks for MDPI

### In Case of Rejection/Comments
- [ ] Save all reviewer feedback
- [ ] Plan revisions based on comments
- [ ] Use feedback to improve project (even if not accepted)

---

## 🎯 Timeline Estimate

| Task | Duration | Start | End |
|------|----------|-------|-----|
| Choose venue + template | 30 min | Morning | 10:30 AM |
| Copy content to template | 45 min | 10:30 AM | 11:15 AM |
| Format figures/tables | 30 min | 11:15 AM | 11:45 AM |
| Grammar + copy-editing | 20 min | 11:45 AM | 12:05 PM |
| Final review | 20 min | 12:05 PM | 12:25 PM |
| Export PDF + submit | 15 min | 12:25 PM | 12:40 PM |
| **TOTAL** | **~2.5 hours** | | |

**You can be done by lunch!** ☕

---

## 🔗 Useful Resources

- **IEEE Xplore:** https://ieeexplore.ieee.org/ — search related papers
- **Sensors Journal (MDPI):** https://www.mdpi.com/journal/sensors — open access
- **Grammarly:** https://grammarly.com — grammar check (free tier)
- **Overleaf:** https://overleaf.com — online LaTeX editor (if using Overleaf template)

---

## 📌 Key Reminders

✅ Keep paper to **4–6 pages** (extended abstract)  
✅ Use **clear language** (avoid buzzwords)  
✅ Make **figures self-contained** (captions should be readable alone)  
✅ Cite **correctly** (IEEE style: [1], [2], etc.)  
✅ Submit **before deadline** (at least 1 hour early)  
✅ Save **confirmation email**  

---

**Good luck with your submission! 🚀**

---

**Questions?** Ask your professor or check the conference FAQ.
