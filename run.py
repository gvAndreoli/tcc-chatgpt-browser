# run.py
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=None, help="Quantos PDFs processar nesta execução")
    args = parser.parse_args()

    from src.pipeline import main  # importa só agora
    main(max_count=args.count)
