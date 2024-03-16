import json
from typing import Dict
from gemini.src.model.parser.base import BaesParser
from gemini.src.misc.utils import extract_code


class ResponseParser(BaesParser):
    """
    Parses response text and extracts relevant data.

    Attributes:
        cookies: Cookies used for parsing.

    Methods:
        parse(response_text: str) -> Dict: Parses the response text and returns a dictionary containing relevant data.
    """

    def __init__(self, cookies: dict) -> None:
        """
        Initializes the ResponseParser object.

        Args:
            cookies (dict): Cookies used for parsing.
        """
        self.cookies = cookies

    def parse(self, response_text: str) -> Dict:
        """
        Parses the response text and extracts relevant data.

        Args:
            response_text (str): The response text to parse.

        Returns:
            Dict: A dictionary containing parsed data.
        """
        return self.parse_response_text(response_text)

    def parse_response_text(self, response_text: str) -> Dict:
        """
        Parses the response text and extracts relevant data.

        Args:
            response_text (str): The response text to parse.

        Returns:
            Dict: A dictionary containing parsed data.
        """
        body = self._extract_body(response_text)

        if not body or not body[4]:
            raise ValueError(
                "Failed to parse response body. Data structure is invalid."
            )

        candidates = self._parse_candidates(body[4])
        metadata = body[1]

        if body[0] is None:
            prompt_class = None
            prompt_candidates = []
        else:
            prompt_class = body[0][0]
            prompt_candidates = body[0][1:] if len(body[0]) > 1 else []

        if not candidates:
            raise ValueError(
                "Failed to generate contents. No output data found in response."
            )

        return {
            "metadata": metadata,
            "prompt_class": prompt_class,
            "prompt_candidates": prompt_candidates,
            "candidates": candidates,
        }

    def _extract_body(self, response_text: str) -> Dict:
        """
        Attempts to extract the body from the response text using three different
        strategies. It stops and returns the body as soon as one of the strategies
        succeeds without raising an error.

        Args:
            response_text (str): The response text to parse.

        Returns:
            Dict: The extracted body.
        """
        parsing_strategies = [
            self.__parse_strategy_1,
            self.__parse_strategy_2,
            self.__parse_strategy_3,
        ]

        for strategy in parsing_strategies:
            try:
                body = strategy(response_text)
                if (
                    body
                ):  # Assuming the strategy returns None or a non-empty dict on success.
                    return body
            except Exception as e:
                # Log or print the exception if needed
                print(f"Parsing failed with strategy {strategy.__name__}: {e}")
                continue

        raise ValueError("All parsing strategies failed.")

    def __parse_strategy_1(self, response_text: str) -> Dict:
        body = json.loads(
            json.loads(response_text.lstrip("')]}'\n\n").split("\n")[1])[0][2]
        )
        if not body[4]:
            body = json.loads(
                json.loads(response_text.lstrip("')]}'\n\n").split("\n")[1])[4][2]
            )
        return body

    def __parse_strategy_2(self, response_text: str) -> Dict:
        body = json.loads(json.loads(response_text.text.split("\n")[2])[0][2])
        if not body[4]:
            body = json.loads(json.loads(response_text.text.split("\n")[2])[4][2])
        else:
            raise ValueError("Invalid response data received.")
        return body

    def __parse_strategy_3(self, response_text: str) -> Dict:
        max_response = max(response_text.split("\n"), key=len)
        body = json.loads(json.loads(max_response)[0][2])
        if not body[4]:
            body = json.loads(json.loads(max_response)[4][2])
        return body

    def _parse_candidates(self, candidates_data: Dict) -> Dict:
        """
        Parses the candidate data.

        Args:
            candidates_data (Dict): The candidate data to parse.

        Returns:
            Dict: The parsed candidate data.
        """
        candidates_list = []
        for candidate_data in candidates_data:
            web_images = self._parse_web_images(candidate_data[4])
            generated_images = self._parse_generated_images(candidate_data[12])
            candidate_dict = {
                "rcid": candidate_data[0],
                "text": candidate_data[1][0],
                "code": self._parse_code(candidate_data[1][0]),
                "web_images": web_images,
                "generated_images": generated_images,
            }
            candidates_list.append(candidate_dict)
        return candidates_list

    def _parse_web_images(self, images_data: Dict) -> Dict:
        """
        Parses web images data.

        Args:
            images_data (Dict): The web images data to parse.

        Returns:
            Dict: The parsed web images data.
        """
        if not images_data:
            return []
        return [
            {
                "url": image[0][0][0],
                "title": image[2],
                "alt": image[0][4],
            }
            for image in images_data
        ]

    def _parse_generated_images(self, images_data: Dict) -> Dict:
        """
        Parses generated images data.

        Args:
            images_data (Dict): The generated images data to parse.

        Returns:
            Dict: The parsed generated images data.
        """
        if not images_data or not images_data[7] or not images_data[7][0]:
            return []
        return [
            {
                "url": image[0][3][3],
                "title": f"[GeneratedImage {image[3][6]}]",
                "alt": image[3][5][i] if len(image[3][5]) > i else image[3][5][0],
                "cookies": self.cookies,
            }
            for i, image in enumerate(images_data[7][0])
        ]


from typing import List


def _parse_code(self, text: str) -> List[str]:
    """
    Parses the provided text to extract code snippets.

    This method checks if the input text is not empty and then attempts to extract
    code snippets from it using the `extract_code` function. If the input text is
    empty, it returns an empty list.

    Parameters:
    - text (str): The text from which code snippets are to be extracted.

    Returns:
    - List[str]: A list of extracted code snippets. Returns an empty list if no
                 code is found or if the input text is empty.

    """
    if not text:
        return []
    return extract_code(text)