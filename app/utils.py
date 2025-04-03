import random
import string


def generate_captcha() -> tuple[str, str]:
    """
    Generate a simple captcha challenge and its answer.

    Returns:
        tuple[str, str]: A tuple containing (challenge_text, answer)
    """
    # Generate a random 5-character string
    chars = string.ascii_uppercase + string.digits
    captcha_answer = ''.join(random.choices(chars, k=5))

    # Create a simple challenge text
    challenge = f"Enter the following characters: {captcha_answer}"

    return challenge, captcha_answer
