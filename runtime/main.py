# main.py
import colorama
from textx import metamodel_from_file

from loader.hydrator import Hydrator
from loader.reporter import ModelReporter
from runtime.engine import Engine
from .tracer import MermaidGenerator, LogColors


def setup_and_load_model():
    """Loads and hydrates the ODPEL model from file."""
    print("-" * 25 + " 1. Loading Model " + "-" * 25)
    odpel_metamodel = metamodel_from_file("dsl/odpel.tx", use_regexp_group=True)
    library_ast = odpel_metamodel.model_from_file("dsl/library.odpl")
    hydrated_model = Hydrator(library_ast, odpel_metamodel).hydrate()
    ModelReporter(hydrated_model).report()
    return hydrated_model


def setup_world_state(engine: Engine):
    """Creates the initial parties and artifacts for the simulation."""
    print("\n" + "-" * 25 + " 2. Setting up World State " + "-" * 25)
    engine.create_party(name="Alice", role_names=["Undergraduate", "Borrower"])
    engine.create_party(name="Libby", role_names=["Librarian"])
    engine.create_party(name="Bob", role_names=["ProxyBorrower"])
    engine.create_artifact_instance(
        artifact_type="LibraryItem",
        instance_id="book-001",
        title="Building Enterprise Systems with ODP",
        itemType="Book",
    )


def run_simulation_scenario(engine: Engine):
    """Executes a sequence of actions to simulate a library scenario."""
    print("\n" + "-" * 25 + " 3. Running Simulation " + "-" * 25)

    # Alice borrows a book, which gives her the 'return_item' burden.
    book_to_borrow = engine.artifacts.get("book-001")
    engine.perform_action("Alice", "borrowItem", item=book_to_borrow)

    the_loan = next(
        (art for art in engine.artifacts.values() if art.template.name == "Loan"), None
    )

    # Librarian tries to fine Alice, but it fails because the loan isn't overdue.
    print("\n--- Librarian attempts to fine Alice (should fail) ---")
    engine.perform_action("Libby", "fineBorrower", loan=the_loan)

    if the_loan:
        # The loan becomes overdue.
        print("\n--- Making loan overdue and re-attempting fine ---")
        the_loan.properties["isOverdue"] = True

        # The librarian now successfully fines Alice, giving her the 'pay_fine' burden.
        engine.perform_action("Libby", "fineBorrower", loan=the_loan)

        # Alice delegates her 'return_item' burden to Bob.
        print("\n--- Alice delegates the return burden to Bob ---")
        bob_party = engine.parties.get("Bob")
        engine.perform_action("Alice", "return_item_delegation", loan=the_loan, agent=bob_party)

        #  Bob, now holding the burden, returns the item.
        print("\n--- Bob returns the item on Alice's behalf ---")
        engine.perform_action("Bob", "proxy_return_item", loan=the_loan)

        # Alice, who still holds the 'pay_fine' burden, pays her fine.
        fine = next(
            (art for art in engine.artifacts.values() if art.template.name == "Fine"),
            None,
        )
        if fine:
            print("\n--- Alice pays her outstanding fine ---")
            engine.perform_action("Alice", "payFine", fine=fine)

def generate_report(engine: Engine):
    """Generates and displays the Mermaid sequence diagram."""
    print("\n" + "-" * 25 + " 4. Generating Report " + "-" * 25)
    generator = MermaidGenerator(engine.tracer.history)
    mermaid_code = generator.generate()

    print("\nhttps://mermaid.live")
    print(f"{LogColors.INFO}{mermaid_code}")


if __name__ == "__main__":
    colorama.init(autoreset=True)

    model = setup_and_load_model()
    engine = Engine(model)
    setup_world_state(engine)
    run_simulation_scenario(engine)
    generate_report(engine)

    colorama.deinit()
