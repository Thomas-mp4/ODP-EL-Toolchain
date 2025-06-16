# main.py
import traceback
import colorama
from textx import metamodel_from_file

from .hydrator import Hydrator
from .reporter import ModelReporter


def main():
    """Main execution function to parse, hydrate, and report on a model."""
    colorama.init(autoreset=True)

    try:
        # Parse the source file into a textX model (AST)
        odpel_metamodel = metamodel_from_file("dsl/odpel.tx", use_regexp_group=True)
        library_ast = odpel_metamodel.model_from_file("dsl/library.odpl")

        # Hydrate the textX model into a rich Python object model
        hydrator = Hydrator(library_ast, odpel_metamodel)
        hydrated_model = hydrator.hydrate()

        # Report on the hydrated model
        reporter = ModelReporter(hydrated_model)
        reporter.report()

    except Exception as ex:
        print(f"\n An unexpected error occurred: {ex}")
        traceback.print_exc()
        print(f"Process aborted.")
        return


if __name__ == "__main__":
    main()
