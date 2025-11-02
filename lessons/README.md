# LangChain/LangGraph Mastery Curriculum

Welcome to the comprehensive LangChain/LangGraph curriculum for building **SpecBot** - an AI-powered specification generation SaaS!

---

## 📚 Course Structure

### **Fully Written Lessons (Ready to Use)**

| Lesson | Title | Duration | File |
|--------|-------|----------|------|
| 0 | Curriculum Overview & Setup | 30 min | [00-CURRICULUM-OVERVIEW.md](./00-CURRICULUM-OVERVIEW.md) |
| 1 | Introduction to LangChain & Basic Prompts | 2 hours | [01-langchain-basics.md](./01-langchain-basics.md) |
| 2 | Chains, Output Parsers & Structured Output | 2 hours | [02-chains-output-parsers.md](./02-chains-output-parsers.md) |
| 3 | Advanced Prompt Engineering & Few-Shot Learning | 2 hours | [03-advanced-prompts.md](./03-advanced-prompts.md) |
| 4 | Introduction to LangGraph & Simple Workflows | 3 hours | [04-langgraph-intro.md](./04-langgraph-intro.md) |

### **Advanced Lessons (5-15)**

| Lesson | Title | Duration | File |
|--------|-------|----------|------|
| 5 | State Management & Data Flow | 3 hours | [05-state-management.md](./05-state-management.md) |
| 6 | Conditional Edges & Routing Logic | 3 hours | [06-conditional-routing.md](./06-conditional-routing.md) |
| 7 | Human-in-the-Loop (HITL) Patterns | 4 hours | [07-hitl-patterns.md](./07-hitl-patterns.md) |
| 8 | Persistence & Checkpointing | 4 hours | [08-checkpointing.md](./08-checkpointing.md) |
| 9 | Error Handling, Retries & Validation | 4 hours | [09-error-handling.md](./09-error-handling.md) |
| 10 | Context7 & Progressive Disclosure | 3 hours | [10-context7-fundamentals.md](./10-context7-fundamentals.md) |
| 11 | RAG for Document Understanding | 4 hours | [11-rag-document-understanding.md](./11-rag-document-understanding.md) |
| 12 | Multi-Document Synthesis | 4 hours | [12-multi-document-synthesis.md](./12-multi-document-synthesis.md) |
| 13 | Template Analysis Pipeline | 5 hours | [13-template-analysis.md](./13-template-analysis.md) |
| 14 | Block-by-Block Generation with HITL | 5 hours | [14-block-generation-hitl.md](./14-block-generation-hitl.md) |
| 15 | Final Integration & Deployment | 6 hours | [15-final-integration.md](./15-final-integration.md) |

### **Reference Documents**

- [LESSONS-6-15-COMPLETE.md](./LESSONS-6-15-COMPLETE.md) - Combined reference for lessons 6-15

---

## 🎯 What You'll Build

Throughout these lessons, you'll build **SpecBot**, a production-ready SaaS that:

1. **Accepts template uploads** (functional spec templates, design docs, etc.)
2. **Analyzes templates automatically** using LLMs
3. **Generates JSON schemas** for each template block
4. **Processes uploaded documents** (PDFs, images, text) using RAG
5. **Generates specifications block-by-block** with human approval gates
6. **Validates output** against schemas
7. **Handles feedback and regeneration** iteratively
8. **Persists workflow state** for resume capability

**Final Architecture**:
```
React Frontend (Approval UI)
         ↓
FastAPI Backend (REST + SSE)
         ↓
LangGraph Workflows (Stateful)
         ↓
PostgreSQL (Checkpoints + Data)
         ↓
S3 (File Storage)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Basic async/await knowledge
- Anthropic or OpenAI API key

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install langchain langchain-anthropic langchain-openai
pip install langgraph
pip install python-dotenv pydantic
pip install psycopg2-binary faiss-cpu pypdf

# Create .env file
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### Start Learning

1. **Read**: [00-CURRICULUM-OVERVIEW.md](./00-CURRICULUM-OVERVIEW.md)
2. **Begin**: [Lesson 1 - LangChain Basics](./01-langchain-basics.md)
3. **Follow the story**: Each lesson builds SpecBot incrementally
4. **Do the exercises**: Hands-on coding is essential
5. **Attempt challenges**: Push your understanding

---

## 📖 Curriculum Phases

### **Phase 1: LangChain Fundamentals (Lessons 1-3)**
**Goal**: Master the building blocks of LangChain

- Prompt templates and variables
- Chains and LCEL syntax
- Output parsers (JSON, Pydantic)
- Few-shot learning
- Chain-of-thought prompting
- Constraint-based generation

**Outcome**: SpecBot can extract structured requirements from natural language.

---

### **Phase 2: LangGraph Basics (Lessons 4-6)**
**Goal**: Build stateful, graph-based workflows

- State management with TypedDict
- Nodes, edges, and transitions
- Conditional routing
- State update strategies
- Fan-out/fan-in patterns
- Multi-way routing

**Outcome**: SpecBot has a multi-step validation workflow with branching logic.

---

### **Phase 3: Advanced LangGraph (Lessons 7-9)**
**Goal**: Production-ready patterns

- Human-in-the-loop (HITL) with `interrupt()`
- Checkpointing with PostgreSQL
- Resume and state history
- Error handling and retries
- Circuit breakers
- Dead letter queues

**Outcome**: SpecBot pauses for approval, recovers from failures, and persists state.

---

### **Phase 4: Context Management & RAG (Lessons 10-12)**
**Goal**: Intelligent context handling

- Context7 patterns
- Progressive disclosure
- Token budget management
- RAG with vector stores
- Multi-document processing
- Contradiction resolution

**Outcome**: SpecBot understands uploaded documents and synthesizes information.

---

### **Phase 5: Building SpecBot Complete (Lessons 13-15)**
**Goal**: Integrate into production system

- Template analysis pipeline
- Block-by-block generation
- HITL approval integration
- FastAPI backend
- React frontend
- Deployment

**Outcome**: Fully deployed SpecBot SaaS ready for users!

---

## 🎓 Learning Path

### For Beginners
1. Start with Lesson 1
2. Complete all exercises
3. Follow the story sequentially
4. Don't skip concepts

### For Experienced Developers
1. Skim Lessons 1-3 if familiar with LangChain
2. Focus on Lessons 4-9 (LangGraph core)
3. Deep dive into Lessons 10-15 (Context & Production)
4. Attempt all challenges

### For Advanced Learners
1. Review curriculum overview
2. Jump to areas of interest
3. Focus on challenges and extensions
4. Build custom features for SpecBot

---

## 🛠️ Project Structure

Recommended project organization:

```
specbot/
├── src/
│   ├── examples/          # Code examples from lessons
│   │   ├── ex01_basic_prompt.py
│   │   ├── ex02_prompt_template.py
│   │   └── ...
│   ├── exercises/         # Your exercise solutions
│   │   ├── ex01_requirement_extractor.py
│   │   ├── ex02_structured_extractor.py
│   │   └── ...
│   ├── specbot/           # Main application code
│   │   ├── workflows/     # LangGraph workflows
│   │   ├── prompts/       # Prompt library
│   │   ├── models/        # Pydantic models
│   │   └── api/           # FastAPI routes
│   └── tests/             # Unit tests
├── lessons/               # This curriculum
├── .env                   # API keys
├── requirements.txt       # Dependencies
└── README.md
```

---

## 📊 Progress Tracking

Use this checklist to track your progress:

### LangChain Fundamentals
- [ ] Lesson 1: Basic prompts and templates
- [ ] Lesson 2: Chains and output parsers
- [ ] Lesson 3: Advanced prompt engineering

### LangGraph Basics
- [ ] Lesson 4: First state graph
- [ ] Lesson 5: State management patterns
- [ ] Lesson 6: Conditional routing

### Advanced LangGraph
- [ ] Lesson 7: Human-in-the-loop
- [ ] Lesson 8: Checkpointing
- [ ] Lesson 9: Error handling

### Context & RAG
- [ ] Lesson 10: Context7 patterns
- [ ] Lesson 11: RAG implementation
- [ ] Lesson 12: Multi-document synthesis

### Final Project
- [ ] Lesson 13: Template analysis
- [ ] Lesson 14: Block generation with HITL
- [ ] Lesson 15: Full deployment

---

## 💡 Tips for Success

1. **Code Along**: Don't just read - type every example yourself
2. **Break Things**: Modify code, introduce bugs, fix them
3. **Use AI Assistants**: Ask Claude/GPT to explain concepts
4. **Build Incrementally**: Each lesson adds to SpecBot
5. **Test Thoroughly**: Run examples before exercises
6. **Review Regularly**: Revisit previous lessons
7. **Join Community**: Share progress, ask questions

---

## 🔗 Additional Resources

### Documentation
- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Anthropic Claude Docs](https://docs.anthropic.com/)
- [OpenAI API Docs](https://platform.openai.com/docs)

### Reference Materials
- [CLAUDE-EXPLAIN.md](../CLAUDE-EXPLAIN.md) - Spec-Kit architecture inspiration
- [Spec-Kit README](../README.md) - Original project documentation

### Community
- [LangChain Discord](https://discord.gg/langchain)
- [LangChain GitHub Discussions](https://github.com/langchain-ai/langchain/discussions)

---

## 🎯 Completion Criteria

You've mastered the curriculum when you can:

✅ Create complex LangChain workflows with structured output
✅ Build stateful LangGraph applications
✅ Implement HITL patterns with persistence
✅ Design production-grade prompts
✅ Handle errors and retries gracefully
✅ Manage context effectively for large documents
✅ Process and understand uploaded files
✅ Deploy a working specification generation system

---

## 🚀 What's Next?

After completing this curriculum:

1. **Extend SpecBot**:
   - Add more template types
   - Implement team collaboration
   - Build version control

2. **Apply to Other Domains**:
   - Test case generation
   - API documentation
   - Technical proposals
   - Requirements analysis

3. **Contribute**:
   - Share improvements to curriculum
   - Create additional exercises
   - Build example projects

4. **Advanced Topics**:
   - Fine-tuning models
   - Custom agents
   - Multi-agent systems
   - Production monitoring

---

## 📞 Support & Feedback

**Questions?** Review the lesson materials and examples first.

**Stuck?** Use AI assistants (Claude, GPT) to explain concepts.

**Found an issue?** Note it and continue - practical learning includes debugging!

---

**Ready to start?** Begin with [Lesson 0: Curriculum Overview](./00-CURRICULUM-OVERVIEW.md)!

**Let's build something amazing together!** 🚀🎓
