import logging
from typing import List, Dict
from modules.pimeye_integration import PimEyeIntegration
from modules.social_media import SocialMediaManager


class DataRetrievalEngine:
    """
    Engine for retrieving personal data from social media platforms and face recognition services.
    """

    def __init__(self, pim_eye_api_key: str):
        """
        Initialize the data retrieval engine.

        :param pim_eye_api_key: API key for the PimEyes-like service.
        """
        self.pim_eye_service = PimEyeIntegration(api_key=pim_eye_api_key)
        self.social_media_manager = SocialMediaManager()

    def process_image(self, image_path: str) -> List[Dict]:
        """
        Process an image to extract data for all faces detected.

        :param image_path: Path to the image file.
        :return: List of detailed information for each detected individual.
        """
        logging.info(f"Processing image: {image_path}")
        image_response = self.pim_eye_service.upload_image(image_path)

        if "id" not in image_response:
            logging.error(f"Failed to process image: {image_response.get('error', 'Unknown error')}")
            return []

        matches = self.pim_eye_service.search_faces(image_response["id"])
        individuals_data = []

        for match in matches:
            individual_data = self.get_individual_data(match)
            if individual_data:
                individuals_data.append(individual_data)

        return individuals_data

    def get_individual_data(self, match: Dict) -> Dict:
        """
        Retrieve detailed personal information for a single match.

        :param match: Match data returned from the PimEyes-like service.
        :return: Aggregated personal information.
        """
        try:
            person_name = match.get("name", "Unknown")
            logging.info(f"Fetching data for: {person_name}")

            # Gather data from social media
            social_data = {
                "facebook": self.social_media_manager.query_facebook(person_name),
                "twitter": self.social_media_manager.query_twitter(person_name),
                "instagram": self.social_media_manager.query_instagram(person_name),
                "linkedin": self.social_media_manager.query_linkedin(person_name),
                "others": self.social_media_manager.query_other_sources(person_name),
            }

            # Combine with match details
            detailed_data = {
                "name": person_name,
                "image_match_details": match,
                "social_media_profiles": social_data,
            }

            logging.info(f"Data retrieved for {person_name}: {detailed_data}")
            return detailed_data

        except Exception as e:
            logging.error(f"Failed to fetch data for match: {e}")
            return {"error": str(e)}

    def generate_report(self, individuals_data: List[Dict]) -> str:
        """
        Generate a detailed report for all individuals detected in the image.

        :param individuals_data: List of individuals' data.
        :return: Report string.
        """
        logging.info("Generating report...")
        report_lines = ["### Detailed Report for Detected Individuals ###"]

        for individual in individuals_data:
            report_lines.append(f"\nName: {individual.get('name', 'Unknown')}")
            report_lines.append("Match Details:")
            report_lines.append(str(individual.get("image_match_details", {})))

            report_lines.append("Social Media Profiles:")
            for platform, profile in individual.get("social_media_profiles", {}).items():
                report_lines.append(f"- {platform.title()}: {profile.get('profile_url', 'Not Found')}")

        report = "\n".join(report_lines)
        logging.info("Report generated successfully.")
        return report


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    data_engine = DataRetrievalEngine(pim_eye_api_key="your_api_key_here")

    # Process an example image
    individuals_data = data_engine.process_image("path/to/your/image.jpg")

    # Generate a report for the detected individuals
    if individuals_data:
        report = data_engine.generate_report(individuals_data)
        print(report)
