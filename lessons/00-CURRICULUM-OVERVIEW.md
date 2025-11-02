# LangChain/LangGraph Mastery: Building SpecBot

> **The Story**: Throughout these lessons, you'll build **SpecBot**, an AI-powered specification generator that helps teams create high-quality functional specifications from natural language descriptions and uploaded documents. By the end, you'll have a working multi-agent system with human-in-the-loop approval, similar to the SaaS platform described in CLAUDE-EXPLAIN.md.

---

## 🎯 Learning Objectives

By completing this curriculum, you will:

1. Master LangChain fundamentals (prompts, chains, models, output parsing)
2. Understand LangGraph architecture (nodes, edges, state management)
3. Implement advanced patterns (HITL, checkpointing, conditional routing)
4. Build production-ready workflows with error handling and validation
5. Integrate Context7 for sophisticated context management
6. Create a complete specification generation system

---

## 📚 Curriculum Structure

### **Phase 1: LangChain Fundamentals (Lessons 1-3)**
Learn the building blocks of LangChain that form the foundation.

- **Lesson 1**: Introduction to LangChain & Basic Prompts
- **Lesson 2**: Chains, Output Parsers & Structured Output
- **Lesson 3**: Advanced Prompt Engineering & Few-Shot Learning

**Story Progress**: Build SpecBot's brain - create intelligent prompts that understand requirements.

---

### **Phase 2: LangGraph Basics (Lessons 4-6)**
Understand graph-based workflows and state management.

- **Lesson 4**: Introduction to LangGraph & Simple Workflows
- **Lesson 5**: State Management & Data Flow
- **Lesson 6**: Conditional Edges & Routing Logic

**Story Progress**: Add structure - create multi-step workflows for specification generation.

---

### **Phase 3: Advanced LangGraph (Lessons 7-9)**
Master complex patterns needed for production systems.

- **Lesson 7**: Human-in-the-Loop (HITL) Patterns
- **Lesson 8**: Persistence & Checkpointing
- **Lesson 9**: Error Handling, Retries & Validation

**Story Progress**: Add reliability - implement approval gates and error recovery.

---

### **Phase 4: Context Management & RAG (Lessons 10-12)**
Learn to manage context effectively with Context7 and RAG patterns.

- **Lesson 10**: Context7 Fundamentals & Progressive Disclosure
- **Lesson 11**: RAG for Document Understanding
- **Lesson 12**: Multi-Document Context Synthesis

**Story Progress**: Add intelligence - teach SpecBot to understand uploaded documents.

---

### **Phase 5: Building SpecBot Complete (Lessons 13-15)**
Integrate everything into a production-ready system.

- **Lesson 13**: Template Analysis Pipeline
- **Lesson 14**: Block-by-Block Generation with HITL
- **Lesson 15**: Final Integration & Deployment

**Story Progress**: Complete the system - deploy a working specification generator!

---

## 🏗️ What You'll Build: SpecBot Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INPUT                          │
│  1. Upload template document                                │
│  2. Upload context files (PDFs, images, docs)              │
│  3. Provide natural language requirements                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              WORKFLOW 1: Template Analysis                  │
│  Extract structure → Classify blocks → Generate prompts    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│           WORKFLOW 2: Specification Generation              │
│  Load context → Generate blocks → HITL approval → Iterate  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    FINAL SPECIFICATION                      │
│  - All blocks approved                                      │
│  - Validated against schema                                 │
│  - Ready for implementation                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Prerequisites

### Required Knowledge
- Python 3.11+
- Basic understanding of async/await
- Familiarity with APIs and HTTP requests
- Basic understanding of AI/LLM concepts

### Tools & Accounts Needed
- Python 3.11+ installed
- API keys:
  - Anthropic API key (Claude models)
  - OR OpenAI API key (GPT models)
- Code editor (VS Code recommended)
- PostgreSQL (for checkpointing in later lessons)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies
pip install langchain langchain-anthropic langchain-openai
pip install langgraph
pip install python-dotenv
pip install pydantic

# For later lessons
pip install psycopg2-binary  # PostgreSQL adapter
pip install faiss-cpu  # Vector store for RAG
pip install pypdf  # PDF processing
pip install python-multipart  # File uploads
```

Create `.env` file:
```bash
ANTHROPIC_API_KEY=your_key_here
# OR
OPENAI_API_KEY=your_key_here
```

---

## 📋 How to Use This Curriculum

### Lesson Structure

Each lesson follows this format:

1. **Concept Introduction** - Theory and explanation
2. **Code Examples** - Annotated examples to study
3. **Hands-On Exercise** - Build something yourself
4. **Challenge** - Stretch goal for advanced learners
5. **Story Progress** - How this fits into SpecBot

### Recommended Approach

1. **Read the concept** - Understand the "why" before the "how"
2. **Study the examples** - Run them, modify them, break them
3. **Complete the exercise** - Build your understanding through practice
4. **Attempt the challenge** - Push your boundaries
5. **Review the solution** - Compare your approach to the provided solution

### Time Estimates

- **Lessons 1-3**: ~6 hours total (2 hours each)
- **Lessons 4-6**: ~9 hours total (3 hours each)
- **Lessons 7-9**: ~12 hours total (4 hours each)
- **Lessons 10-12**: ~12 hours total (4 hours each)
- **Lessons 13-15**: ~15 hours total (5 hours each)

**Total**: ~54 hours (can be spread over 2-3 weeks)

---

## 🎓 Completion Criteria

You'll know you've mastered the material when you can:

- ✅ Create complex multi-step LangChain workflows
- ✅ Build LangGraph workflows with conditional logic
- ✅ Implement human-in-the-loop patterns with persistence
- ✅ Design prompts that produce consistent, structured output
- ✅ Handle errors gracefully with retries and validation
- ✅ Manage context effectively for large document processing
- ✅ Deploy a working specification generation system

---

## 🚀 Getting Started

Ready to begin? Start with:

**[Lesson 1: Introduction to LangChain & Basic Prompts →](./01-langchain-basics.md)**

---

## 📖 Additional Resources

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [Context7 Patterns](https://github.com/context7) (if available)
- [CLAUDE-EXPLAIN.md](../CLAUDE-EXPLAIN.md) - Reference architecture

---

## 💡 Tips for Success

1. **Code along** - Don't just read, type the code yourself
2. **Experiment** - Change parameters, break things, fix them
3. **Ask questions** - Use AI assistants to clarify concepts
4. **Build incrementally** - Each lesson builds on the previous
5. **Take breaks** - Complex topics need time to sink in
6. **Review regularly** - Revisit earlier lessons as you progress

---

## 🎯 Final Project Preview

By Lesson 15, you'll have built **SpecBot** with these features:

- ✨ Upload any specification template
- 🤖 AI analyzes structure and generates generation prompts
- 📄 Processes uploaded context documents (PDFs, images, text)
- 🔄 Generates specifications block-by-block
- ✋ Human approval gates for each block
- 🔁 Regeneration based on feedback
- ✅ JSON schema validation
- 💾 Persistent workflows (resume after interruption)
- 🎨 Export to multiple formats

**Let's build something amazing!** 🚀

---

## License & Credits

This curriculum is inspired by the Spec-Kit architecture and the patterns described in CLAUDE-EXPLAIN.md. All code examples are provided for educational purposes.

**Happy Learning!** 🎓
