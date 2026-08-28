# Devin/cyber_law/warrant_generator.py
# Purpose: A tool to generate a formal PDF Penetration Testing Authorization
#          Agreement based on user-provided engagement details.

import logging
from datetime import datetime
from typing import List

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from modules.user_interaction_module import UserInteractionManager
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("WarrantGenerator")
# (Logger setup omitted for brevity)

class PentestAuthorizationDoc:
    """Generates the PDF authorization document."""
    def __init__(self, client_name, client_address, consultant_name, target_scope, start_date, end_date):
        self.details = locals()

    def generate_pdf(self, output_path: str):
        """Creates the PDF file using reportlab."""
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        
        def write_text(y_pos, text, font="Helvetica", size=11):
            text_obj = c.beginText(1 * inch, height - y_pos * inch)
            text_obj.setFont(font, size)
            for line in text.split('\n'):
                text_obj.textLine(line)
            c.drawText(text_obj)

        # --- Document Content ---
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2.0, height - 1*inch, "Penetration Testing Authorization Agreement")

        write_text(1.5, "This document confirms the authorization for a security assessment.", "Helvetica-Bold", 12)
        
        # Parties
        write_text(2.0, "1. Parties Involved", "Helvetica-Bold")
        parties_text = (f"  - The Client: {self.details['client_name']}, located at {self.details['client_address']}.\n"
                        f"  - The Consultant: {self.details['consultant_name']}.")
        write_text(2.2, parties_text)

        # Scope
        write_text(3.0, "2. Scope of Testing", "Helvetica-Bold")
        scope_text = ("The Consultant is authorized to perform penetration testing activities against the following targets ONLY:\n"
                      + "\n".join([f"  - {target}" for target in self.details['target_scope']]))
        write_text(3.2, scope_text)
        
        # Timeframe
        write_text(4.5, "3. Authorization Period", "Helvetica-Bold")
        time_text = (f"This authorization is valid from {self.details['start_date']} to {self.details['end_date']}.")
        write_text(4.7, time_text)
        
        # Signatures
        write_text(8.0, "4. Signatures", "Helvetica-Bold")
        c.line(1.5*inch, height - 8.5*inch, 4*inch, height - 8.5*inch)
        write_text(8.7, "Client Authorized Signature")
        c.line(5*inch, height - 8.5*inch, 7.5*inch, height - 8.5*inch)
        write_text(8.7, "Consultant Signature", font="Helvetica-Oblique")


        c.save()
        logger.info(f"PDF document successfully generated at '{output_path}'.")

class WarrantGenerator:
    """Orchestrates the creation of a new authorization document."""
    def __init__(self, interaction_manager: UserInteractionManager):
        if not DEPS_AVAILABLE:
            raise ImportError(f"Required libraries missing. Run 'pip install reportlab'. Error: {_import_error}")
        self.uim = interaction_manager

    def create_new_warrant(self):
        """Runs an interactive wizard to gather details and generate the PDF."""
        print("--- Penetration Test Authorization Wizard ---")
        client_name = self.uim.get_user_input("Enter the client's full legal name:")
        client_addr = self.uim.get_user_input("Enter the client's address:")
        consultant_name = self.uim.get_user_input("Enter the consultant's name (your name/company):")
        scope_str = self.uim.get_user_input("Enter target IPs/domains (comma-separated):")
        start_date = self.uim.get_user_input("Enter the engagement start date (e.g., YYYY-MM-DD):")
        end_date = self.uim.get_user_input("Enter the engagement end date (e.g., YYYY-MM-DD):")
        
        doc = PentestAuthorizationDoc(
            client_name=client_name,
            client_address=client_addr,
            consultant_name=consultant_name,
            target_scope=[s.strip() for s in scope_str.split(',')],
            start_date=start_date,
            end_date=end_date
        )
        
        output_filename = f"Pentest_Authorization_{client_name.replace(' ', '_')}.pdf"
        doc.generate_pdf(output_filename)
        return output_filename

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Pentest Authorization Generator Demo ⚖️📄 ===")
    print("=========================================================")
    
    if not DEPS_AVAILABLE:
        print(f"ERROR: A required dependency is missing: {_import_error}")
        print("Please run: 'pip install reportlab'")
    else:
        try:
            generator = WarrantGenerator(interaction_manager=UserInteractionManager())
            generated_file = generator.create_new_warrant()
            print(f"\nAuthorization document has been created: '{generated_file}'")
        except Exception as e:
            logger.error(f"Demo failed to run: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== Warrant Generator Demo Complete ===")
    print("=========================================================")
