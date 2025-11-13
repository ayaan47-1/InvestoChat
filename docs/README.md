# InvestoChat Documentation

Complete documentation for the InvestoChat RAG system.

## 📁 Documentation Structure

### [Setup Guides](setup/) - Getting Started
Initial setup and installation documentation:
- **[SETUP_COMPLETE.md](setup/SETUP_COMPLETE.md)** - Database schema and initial setup verification
- **[INGESTION_COMPLETE.md](setup/INGESTION_COMPLETE.md)** - Complete ingestion pipeline walkthrough
- **[FRONTEND_SETUP.md](setup/FRONTEND_SETUP.md)** - Frontend configuration (if applicable)

### [User Guides](guides/) - How-To Documentation
Practical guides for using the system:
- **[QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md)** - Quick command reference for common tasks
- **[QUICK_COMMANDS.md](guides/QUICK_COMMANDS.md)** - Essential commands with examples
- **[TESTING_GUIDE.md](guides/TESTING_GUIDE.md)** - How to test retrieval and RAG functionality
- **[TABLE_EXTRACTION_GUIDE.md](guides/TABLE_EXTRACTION_GUIDE.md)** - Using the table extraction system
- **[N8N_AUTOMATION_GUIDE.md](guides/N8N_AUTOMATION_GUIDE.md)** - Automating workflows with n8n
- **[CURATED_FACTS_GUIDE.md](guides/CURATED_FACTS_GUIDE.md)** - Managing high-precision curated answers
- **[IMAGE_SUPPORT_GUIDE.md](guides/IMAGE_SUPPORT_GUIDE.md)** - Processing images and visual content

### [Analysis Documents](analysis/) - Technical Deep Dives
Performance analysis and enhancement documentation:
- **[ENHANCEMENT_ANALYSIS.md](analysis/ENHANCEMENT_ANALYSIS.md)** - RAG system enhancement analysis
- **[TIER1_ENHANCEMENTS.md](analysis/TIER1_ENHANCEMENTS.md)** - Implemented Tier 1 improvements
- **[OCR_PAGES_ANALYSIS.md](analysis/OCR_PAGES_ANALYSIS.md)** - OCR quality and coverage analysis
- **[RAG_TEST_RESULTS.md](analysis/RAG_TEST_RESULTS.md)** - Retrieval performance test results
- **[TABLE_SYSTEM_COMPLETE.md](analysis/TABLE_SYSTEM_COMPLETE.md)** - Table extraction implementation results

## 🚀 Quick Navigation

**Just getting started?**
1. [Setup Complete](setup/SETUP_COMPLETE.md) - Verify your environment
2. [Quick Commands](guides/QUICK_COMMANDS.md) - Learn essential commands
3. [Testing Guide](guides/TESTING_GUIDE.md) - Test your installation

**Want to automate?**
→ [n8n Automation Guide](guides/N8N_AUTOMATION_GUIDE.md)

**Need to extract tables?**
→ [Table Extraction Guide](guides/TABLE_EXTRACTION_GUIDE.md)

**Want to improve accuracy?**
→ [Enhancement Analysis](analysis/ENHANCEMENT_ANALYSIS.md)

## 📊 Documentation by Task

### Setting Up the System
- Database setup → [SETUP_COMPLETE.md](setup/SETUP_COMPLETE.md)
- Running first ingestion → [INGESTION_COMPLETE.md](setup/INGESTION_COMPLETE.md)
- Environment validation → See `../InvestoChat_Build/test_env.py`

### Daily Operations
- Processing PDFs → [QUICK_COMMANDS.md](guides/QUICK_COMMANDS.md)
- Running queries → [QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md)
- Testing retrieval → [TESTING_GUIDE.md](guides/TESTING_GUIDE.md)

### Advanced Features
- Table extraction → [TABLE_EXTRACTION_GUIDE.md](guides/TABLE_EXTRACTION_GUIDE.md)
- Curated facts → [CURATED_FACTS_GUIDE.md](guides/CURATED_FACTS_GUIDE.md)
- Automation → [N8N_AUTOMATION_GUIDE.md](guides/N8N_AUTOMATION_GUIDE.md)

### Performance Analysis
- Retrieval improvements → [TIER1_ENHANCEMENTS.md](analysis/TIER1_ENHANCEMENTS.md)
- Test results → [RAG_TEST_RESULTS.md](analysis/RAG_TEST_RESULTS.md)
- Table system → [TABLE_SYSTEM_COMPLETE.md](analysis/TABLE_SYSTEM_COMPLETE.md)

## 🔗 Related Resources

- **Main README**: [../README.md](../README.md)
- **Claude Instructions**: [../CLAUDE.md](../CLAUDE.md)
- **Utility Scripts**: [../scripts/](../scripts/)
- **Source Code**: [../InvestoChat_Build/](../InvestoChat_Build/)

## 📝 Contributing to Docs

When adding new documentation:
- **Setup/installation guides** → `setup/`
- **User how-to guides** → `guides/`
- **Technical analysis** → `analysis/`

Update this index when adding new files!
