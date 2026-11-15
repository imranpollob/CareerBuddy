"""Server-only answer keys. Objective grading never uses model output."""
from backend.tools.jobs import SKILLS

# (prompt, choices, correct index, feedback). Only public_questions leaves this module.
BANK = {
    "python": [
        ("What is the result of [n * 2 for n in range(3)]?", ["[0, 2, 4]", "[2, 4, 6]", "[0, 1, 2]", "An iterator"], 0, "range(3) yields 0, 1, 2; the comprehension doubles each value."),
        ("Which data structure stores unique values?", ["list", "tuple", "set", "str"], 2, "A set stores unique, hashable values."),
        ("What does a context manager's with statement ensure?", ["Parallel execution", "Cleanup via __exit__", "No exceptions", "Immutable variables"], 1, "__exit__ runs when the with block exits, including on exceptions."),
        ("Which pattern avoids a shared mutable default argument?", ["def f(x=[])", "def f(x={})", "A global list", "def f(x=None), then create a list inside"], 3, "Default arguments are evaluated once. Create a fresh mutable value inside the function."),
    ],
    "rag": [
        ("What does retrieval add to an LLM application?", ["Automatic fine-tuning", "Relevant external context", "Guaranteed truth", "Unlimited tokens"], 1, "Retrieval supplies relevant context at inference time."),
        ("Why split long documents into chunks?", ["Remove citations", "Change model weights", "Retrieve focused passages within context limits", "Encrypt documents"], 2, "Chunks allow focused retrieval and fit within token budgets."),
        ("How should a grounded answer expose its supporting evidence?", ["Cite retrieved sources", "Hide source text", "Invent a URL", "Use confidence alone"], 0, "Citations let users check supporting passages."),
        ("A relevant document contains 'ignore all rules'. What should the app do?", ["Execute it", "Send secrets", "Disable validation", "Treat it as untrusted source data"], 3, "Retrieved text is data, never a privileged instruction."),
    ],
    "llm": [
        ("Which message defines the assistant's application-level behavior?", ["Tool result", "User message", "System message", "Citation"], 2, "System instructions establish application behavior."),
        ("What is a token budget used for?", ["Limiting context and output size", "Database backups", "Authentication", "GPU drivers"], 0, "Models have bounded input and output token limits."),
        ("How should a tool-call argument be handled?", ["Trust it always", "Execute arbitrary code", "Ignore its type", "Validate it against a schema"], 3, "Tool-call arguments must be validated and authorized in code."),
        ("Which setting generally reduces variation in generation?", ["More tokens", "Lower temperature", "More tools", "Longer URLs"], 1, "Lower temperature generally makes sampling less variable."),
    ],
    "pytorch": [
        ("Which object is the basic numerical container in PyTorch?", ["DataFrame", "Tensor", "DOM node", "Cursor"], 1, "Tensors hold multidimensional numeric data."),
        ("What does loss.backward() compute?", ["New labels", "A database index", "Gradients", "A model upload"], 2, "Autograd computes gradients of loss with respect to parameters."),
        ("Why call optimizer.zero_grad() in a typical training loop?", ["Reset accumulated gradients", "Delete weights", "Disable training", "Load data"], 0, "Gradients accumulate by default and should be reset between steps."),
        ("Which context avoids gradient tracking during inference?", ["model.train()", "loss.backward()", "optimizer.step()", "torch.no_grad()"], 3, "no_grad disables gradient tracking to reduce inference overhead."),
    ],
    "aws": [
        ("Where should a local app obtain AWS credentials?", ["Browser source", "A public repository", "The standard SDK credential chain", "A job description"], 2, "Use SDK credential providers; never put AWS secrets in frontend code."),
        ("Which service provides managed foundation-model inference?", ["Amazon Bedrock", "Route 53", "CloudFront", "EBS"], 0, "Bedrock provides managed foundation-model inference APIs."),
        ("Which IAM policy follows least privilege?", ["Allow all actions", "AdministratorAccess", "Share root keys", "Only required actions on required resources"], 3, "Grant only the operations and resources the application needs."),
        ("What uniquely identifies an item in this DynamoDB table?", ["Its array index", "Partition key and sort key", "Its display name", "Its color"], 1, "The composite primary key is PK plus SK."),
    ],
    "evaluation": [
        ("How should objective multiple-choice answers be graded?", ["By model opinion", "With a server-held answer key", "By the candidate", "With a random score"], 1, "Deterministic grading makes objective results reproducible."),
        ("What does a trajectory evaluation inspect?", ["Only color", "Only latency", "Tool use and execution order", "CSS size"], 2, "Trajectory checks verify the agent followed the intended workflow."),
        ("Which data is appropriate for a held-out evaluation?", ["Examples excluded from training", "Only training examples", "Invented scores", "User passwords"], 0, "Held-out examples help measure generalization."),
        ("What should a RAG evaluation check?", ["Only response length", "Only fluency", "Only font", "Retrieval relevance and answer grounding"], 3, "Useful RAG evaluations measure retrieval quality and support for answers."),
    ],
    "sql": [
        ("Which clause filters rows before aggregation?", ["ORDER BY", "WHERE", "HAVING", "LIMIT"], 1, "WHERE filters input rows before GROUP BY."),
        ("Which JOIN retains all rows from the left table?", ["INNER JOIN", "CROSS JOIN", "LEFT JOIN", "SELF JOIN"], 2, "LEFT JOIN preserves unmatched left rows with NULL right values."),
        ("How should user input enter a SQL query?", ["Bound parameters", "String concatenation", "eval()", "A public URL"], 0, "Bound parameters prevent input from being interpreted as SQL syntax."),
        ("Which expression counts every row including rows with NULLs?", ["COUNT(column)", "SUM(column)", "AVG(column)", "COUNT(*)"], 3, "COUNT(*) counts all rows; COUNT(column) ignores NULL values."),
    ],
}

LESSONS = {
    "python": ("Reliable Python foundations", "A comprehension transforms each element: [n * 2 for n in range(3)] gives [0, 2, 4]. Sets remove duplicates. Use with open(...) to close files even after an exception. Use None as a default and construct a new list inside the function to avoid shared state.", "Write a function unique_doubles(values=None) that returns a set of doubled inputs. Explain why its default should be None."),
    "rag": ("Build a grounded retrieval loop", "Split a document into focused chunks. Retrieve passages relevant to the question, provide them as context, and cite their source IDs in the answer. Treat retrieved instructions as untrusted data. If evidence is missing, say so instead of inventing a source.", "Sketch a retrieve(question) → context → answer flow. Add source URLs and describe how you would reject instructions embedded in a document."),
    "llm": ("Safe LLM application patterns", "System messages define application behavior. Tokens bound input and output size; budget both. A model's tool arguments are untrusted and need schema validation and authorization. Lower temperature generally reduces sampling variation.", "Design a tool schema for looking up a job by ID. List which authorization checks belong in Python."),
    "pytorch": ("A small PyTorch training loop", "A tensor is PyTorch's numerical container. A typical iteration calls optimizer.zero_grad(), computes a prediction and loss, calls loss.backward() to calculate gradients, then optimizer.step(). Use torch.no_grad() for inference when gradients are unnecessary.", "Write the five steps of a training iteration and explain why gradients must be reset."),
    "aws": ("Use Bedrock with least privilege", "Use boto3's credential chain on the server. Amazon Bedrock provides managed inference. Grant only required IAM actions and resources. This application's DynamoDB table identifies each record with both PK and SK.", "Describe the credentials, region, model ID, and IAM permissions needed for a local Converse call."),
    "evaluation": ("Evaluate behavior and evidence", "Grade objective answers with server-held keys. Use held-out examples to check generalization. Inspect agent trajectories for appropriate tool selection and order. For RAG, evaluate both retrieval relevance and whether answers are grounded in retrieved evidence.", "Write two trajectory expectations and two grounding checks for a career-advice agent."),
    "sql": ("Query data safely", "WHERE filters before aggregation; HAVING filters groups. A LEFT JOIN retains every left-side row. Use bound parameters for user input. COUNT(*) includes all rows, while COUNT(column) excludes NULL values in that column.", "Write a parameterized query that finds a candidate's assessment attempts, including skills with no attempts."),
}


def public_questions(skill):
    return [{"id": f"q{i+1}", "prompt": q[0], "choices": q[1]} for i, q in enumerate(BANK[skill])]


def grade(skill, answers):
    expected = {f"q{i+1}" for i in range(len(BANK[skill]))}
    if set(answers) != expected or any(type(v) is not int or v not in range(4) for v in answers.values()):
        raise ValueError("Submit one valid choice (0–3) for every question, with no extra questions")
    feedback = [{"question_id": f"q{i+1}", "correct": answers[f"q{i+1}"] == q[2],
                 "explanation": q[3]} for i, q in enumerate(BANK[skill])]
    score = 100 * sum(f["correct"] for f in feedback) // len(feedback)
    return {"score": score, "passed": score >= 75, "feedback": feedback,
            "scope": f"Four-question {SKILLS[skill]} fundamentals assessment; not a professional certification"}
