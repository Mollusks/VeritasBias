import unittest

from bias_detector import detect_bias, extract_text_from_url


class BiasDetectorTests(unittest.TestCase):
    def test_progressive_language_detects_left_leaning(self):
        result = detect_bias("We need universal healthcare, a fair minimum wage, and stronger worker protections.")
        self.assertEqual(result["overall_label"], "Progressive / Left")

    def test_healthcare_language_does_not_suggest_green_party(self):
        result = detect_bias("We need universal healthcare, paid leave, and stronger labor protections.")
        party_names = [party["name"] for party in result["party_candidates"]]
        self.assertNotIn("Green Party", party_names)

    def test_green_language_detects_ecosocialist_leaning(self):
        result = detect_bias("We need climate justice, a green new deal, and a just transition to renewable energy.")
        self.assertEqual(result["overall_label"], "Green / Eco-Socialist")
        self.assertIn("Green Party", [party["name"] for party in result["party_candidates"]])

    def test_conservative_language_detects_right_leaning(self):
        result = detect_bias("We need tax cuts, family values, strong borders, and limited government.")
        self.assertEqual(result["overall_label"], "Conservative / Right")

    def test_non_literal_left_language_still_detects_progressive_leaning(self):
        result = detect_bias("We need affordable health coverage, stronger pay for workers, and protections for labor unions.")
        self.assertEqual(result["overall_label"], "Progressive / Left")

    def test_non_literal_conservative_language_still_detects_right_leaning(self):
        result = detect_bias("We need lower taxes, protect our borders, defend family life, and keep the state out of everyday decisions.")
        self.assertEqual(result["overall_label"], "Conservative / Right")

    def test_policy_action_phrases_detect_left_leaning(self):
        result = detect_bias("Raising the minimum wage and expanding union protections would help workers and reduce inequality.")
        self.assertEqual(result["overall_label"], "Progressive / Left")

    def test_policy_action_phrases_detect_libertarian_leaning(self):
        result = detect_bias("The government should stay out of private life and cut regulations that invade civil liberties.")
        self.assertEqual(result["overall_label"], "Libertarian")

    def test_libertarian_language_detects_libertarian_leaning(self):
        result = detect_bias("We should protect civil liberties, reduce regulation, and defend individual freedom.")
        self.assertEqual(result["overall_label"], "Libertarian")

    def test_extract_text_from_url_removes_html_noise(self):
        html = """
        <html><head><title>Example</title></head>
        <body>
        <h1>Healthcare for Families</h1>
        <p>We need universal healthcare and workers rights.</p>
        <script>ignored</script>
        </body></html>
        """
        text = extract_text_from_url("data:text/html," + html)
        self.assertIn("Healthcare for Families", text)
        self.assertIn("universal healthcare", text.lower())
        self.assertNotIn("ignored", text.lower())


if __name__ == "__main__":
    unittest.main()
