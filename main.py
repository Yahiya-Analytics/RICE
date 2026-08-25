# main.py
from parser.parser import Parser
from orchestrator.orchestrator import Orchestrator

def main():
    # 1. parse toml
    config = Parser("rice.toml").parse()

    # 2. run pipeline with a test query
    query  = "What is this document about?"
    orchestrator = Orchestrator(config)
    answer, sources = orchestrator.run(query)

    # 3. print result
    print("\n Answer:")
    print(answer)

    print("\n Sources:")
    for i, src in enumerate(sources):
        print(f"  [{i+1}] {src['metadata'].get('source')} "
              f"p.{src['metadata'].get('page')} "
              f"score={src['score']:.3f}")

if __name__ == "__main__":
    main()