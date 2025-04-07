from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the model and components
model_path = './legal_argument_linker_model'

# Initialize global variables
model = None
feature_extractor = None
sentence_model = None
feature_cols = None

# Define feature extractor class
class ArgumentFeatureExtractor:
    def __init__(self, sentence_model):
        self.sentence_model = sentence_model
        
    def get_argument_embedding(self, arg):
        """Get semantic embedding for an argument"""
        heading = arg['heading']
        content = arg['content']
        
        # Truncate content if too long for embedding model
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length]
        
        # Repeat heading to give it more weight
        text_to_embed = heading + " " + heading + " " + content
        
        # Get embedding
        embedding = self.sentence_model.encode(text_to_embed)
        return embedding
    
    def get_heading_embedding(self, heading):
        """Get semantic embedding for a heading only"""
        return self.sentence_model.encode(heading)
    
    def calculate_semantic_similarity(self, moving_arg, response_arg):
        """Calculate semantic similarity between arguments"""
        moving_embedding = self.get_argument_embedding(moving_arg)
        response_embedding = self.get_argument_embedding(response_arg)
        
        return cosine_similarity([moving_embedding], [response_embedding])[0][0]
    
    def calculate_heading_similarity(self, moving_arg, response_arg):
        """Calculate similarity between argument headings"""
        moving_heading_emb = self.get_heading_embedding(moving_arg['heading'])
        response_heading_emb = self.get_heading_embedding(response_arg['heading'])
        
        return cosine_similarity([moving_heading_emb], [response_heading_emb])[0][0]
    
    def extract_legal_citations(self, text):
        """Extract legal citations from text using regex patterns"""
        citation_patterns = [
            # Case citations (e.g., Brown v. Board of Education)
            r'[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+',
            
            # Supreme Court citations (e.g., 347 U.S. 483)
            r'\d+\s+U\.S\.\s+\d+',
            
            # Federal Reporter citations (e.g., 865 F.3d 211)
            r'\d+\s+F\.\d+d\s+\d+',
            
            # Supreme Court Reporter citations (e.g., 137 S.Ct. 2012)
            r'\d+\s+S\.Ct\.\s+\d+',
            
            # Federal Rules citations (e.g., Fed. R. Civ. P. 12(b)(6))
            r'Fed\.\s+R\.\s+Civ\.\s+P\.\s+\d+(\([a-z]\))+',
            
            # U.S. Code citations (e.g., 42 U.S.C. § 1983)
            r'\d+\s+U\.S\.C\.\s+§\s+\d+',
            
            # Code of Federal Regulations (e.g., 17 C.F.R. § 240.10b-5)
            r'\d+\s+C\.F\.R\.\s+§\s+\d+\.\d+[a-z]?-\d+'
        ]
        
        citations = []
        for pattern in citation_patterns:
            citations.extend(re.findall(pattern, text))
        
        return set(citations)
    
    def calculate_citation_overlap(self, moving_arg, response_arg):
        """Calculate the overlap in legal citations"""
        moving_citations = self.extract_legal_citations(moving_arg['content'])
        response_citations = self.extract_legal_citations(response_arg['content'])
        
        # Calculate Jaccard similarity
        if not moving_citations or not response_citations:
            return 0.0
        
        intersection = len(moving_citations.intersection(response_citations))
        union = len(moving_citations.union(response_citations))
        
        return intersection / union if union > 0 else 0.0
    
    def extract_key_terms(self, text):
        """Extract key legal terms based on frequency in the document"""
        # Simple implementation - split by space and filter by length
        words = text.lower().split()
        words = [w for w in words if len(w) > 3]  # Filter short words
        
        # Count frequencies
        from collections import Counter
        term_counts = Counter(words)
        
        # Get top terms
        top_terms = [term for term, count in term_counts.most_common(50)]
        
        return set(top_terms)
    
    def calculate_term_overlap(self, moving_arg, response_arg):
        """Calculate the overlap in key legal terms"""
        moving_terms = self.extract_key_terms(moving_arg['content'])
        response_terms = self.extract_key_terms(response_arg['content'])
        
        # Calculate Jaccard similarity
        if not moving_terms or not response_terms:
            return 0.0
        
        intersection = len(moving_terms.intersection(response_terms))
        union = len(moving_terms.union(response_terms))
        
        return intersection / union if union > 0 else 0.0
    
    def extract_entities(self, text):
        """Extract simple entities (placeholder function)"""
        # This is a simplified entity extraction
        # In a production system, you would use a proper NER model
        entities = set()
        
        # Extract capitalized phrases as potential entities
        entity_pattern = r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\b'
        potential_entities = re.findall(entity_pattern, text)
        
        # Filter by length
        entities.update([e for e in potential_entities if len(e) > 3])
        
        return entities
    
    def calculate_entity_overlap(self, moving_arg, response_arg):
        """Calculate the overlap in entities"""
        moving_entities = self.extract_entities(moving_arg['content'])
        response_entities = self.extract_entities(response_arg['content'])
        
        # Calculate Jaccard similarity
        if not moving_entities or not response_entities:
            return 0.0
        
        intersection = len(moving_entities.intersection(response_entities))
        union = len(moving_entities.union(response_entities))
        
        return intersection / union if union > 0 else 0.0
    
    def extract_all_features(self, moving_arg, response_arg):
        """Extract all features for a pair of arguments"""
        features = {
            'semantic_similarity': self.calculate_semantic_similarity(moving_arg, response_arg),
            'heading_similarity': self.calculate_heading_similarity(moving_arg, response_arg),
            'citation_overlap': self.calculate_citation_overlap(moving_arg, response_arg),
            'entity_overlap': self.calculate_entity_overlap(moving_arg, response_arg),
            'term_overlap': self.calculate_term_overlap(moving_arg, response_arg)
        }
        
        return features

def load_models():
    """Load models and components"""
    global model, feature_extractor, sentence_model, feature_cols
    
    try:
        # Load configuration
        config_path = os.path.join(model_path, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                feature_cols = config.get('feature_cols', [
                    'semantic_similarity', 
                    'heading_similarity', 
                    'citation_overlap', 
                    'entity_overlap', 
                    'term_overlap'
                ])
        else:
            # Default feature columns if config not found
            feature_cols = [
                'semantic_similarity', 
                'heading_similarity', 
                'citation_overlap', 
                'entity_overlap', 
                'term_overlap'
            ]
            print("Configuration file not found. Using default features.")
        
        # Load sentence transformer model
        print("Loading sentence transformer model...")
        sentence_model = SentenceTransformer('all-mpnet-base-v2')
        
        # Load classifier model
        model_file = os.path.join(model_path, 'model.pkl')
        if os.path.exists(model_file):
            print("Loading saved model...")
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
        else:
            # Use a placeholder model if saved model not found
            print("Model file not found. Using a placeholder model.")
            from sklearn.linear_model import LogisticRegression
            model = LogisticRegression(class_weight='balanced')
        
        # Initialize feature extractor
        feature_extractor = ArgumentFeatureExtractor(sentence_model)
        
        print("Models and components loaded successfully")
        return True
    
    except Exception as e:
        print(f"Error loading models: {str(e)}")
        return False

# API routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    global model, feature_extractor, sentence_model
    models_loaded = model is not None and feature_extractor is not None and sentence_model is not None
    
    return jsonify({
        "status": "healthy", 
        "models_loaded": models_loaded
    })

@app.route('/api/extract-arguments', methods=['POST'])
def extract_arguments():
    """
    Extract arguments from text or documents
    Input: JSON with 'moving_text' and 'response_text' fields
    Output: JSON with extracted arguments from both texts
    """
    try:
        data = request.json
        
        # Get text from request
        moving_text = data.get('moving_text', '')
        response_text = data.get('response_text', '')
        
        # Function to extract arguments from text
        def extract_arguments_from_text(text):
            # Split text into paragraphs
            paragraphs = text.split('\n\n')
            
            arguments = []
            current_heading = None
            current_content = []
            
            for para in paragraphs:
                # Skip empty paragraphs
                if not para.strip():
                    continue
                    
                # Check if paragraph looks like a heading:
                # - All caps
                # - Short (less than 100 chars)
                # - Ends with period but doesn't have many periods
                is_heading = (para.isupper() or 
                             (len(para) < 100 and para.count('.') <= 1) or
                             (para.endswith('.') and para.count('.') == 1))
                
                if is_heading:
                    # If we have a previous heading and content, save it
                    if current_heading and current_content:
                        arguments.append({
                            "heading": current_heading,
                            "content": '\n\n'.join(current_content)
                        })
                        
                    # Start new argument
                    current_heading = para
                    current_content = []
                else:
                    # Add paragraph to current content
                    if current_heading:
                        current_content.append(para)
                    else:
                        # If no heading yet, treat this as a heading
                        current_heading = para
            
            # Add the last argument if there is one
            if current_heading and current_content:
                arguments.append({
                    "heading": current_heading,
                    "content": '\n\n'.join(current_content)
                })
                
            return arguments
        
        # Extract arguments from both texts
        moving_arguments = extract_arguments_from_text(moving_text)
        response_arguments = extract_arguments_from_text(response_text)
        
        return jsonify({
            "moving_brief": {
                "brief_id": "moving_brief",
                "brief_arguments": moving_arguments
            },
            "response_brief": {
                "brief_id": "response_brief",
                "brief_arguments": response_arguments
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/link-arguments', methods=['POST'])
def link_arguments():
    """
    Link arguments between moving and response briefs
    Input: JSON with moving_brief and response_brief objects
    Output: JSON with linked argument pairs and confidence scores
    """
    try:
        # Check if models are loaded
        global model, feature_extractor, sentence_model, feature_cols
        if model is None or feature_extractor is None or sentence_model is None:
            success = load_models()
            if not success:
                return jsonify({"error": "Failed to load models"}), 500
        
        data = request.json
        
        # Get parameters
        threshold = float(data.get('threshold', 0.4))
        max_links = int(data.get('max_links_per_arg', 5))
        
        # Prepare briefs
        moving_brief = data.get('moving_brief', {})
        response_brief = data.get('response_brief', {})
        
        # Validate input
        if 'brief_arguments' not in moving_brief or 'brief_arguments' not in response_brief:
            return jsonify({"error": "Invalid brief format. 'brief_arguments' field required."}), 400
        
        moving_args = moving_brief['brief_arguments']
        response_args = response_brief['brief_arguments']
        
        if not moving_args or not response_args:
            return jsonify({"error": "No arguments found in briefs."}), 400
        
        # Extract features for all possible argument pairs
        all_pairs = []
        pair_details = []
        
        for m_idx, moving_arg in enumerate(moving_args):
            for r_idx, response_arg in enumerate(response_args):
                features = feature_extractor.extract_all_features(moving_arg, response_arg)
                
                # Store feature values for classification
                feature_values = [features[col] for col in feature_cols]
                all_pairs.append(feature_values)
                
                # Store details for each pair
                pair_details.append({
                    'moving_idx': m_idx,
                    'moving_heading': moving_arg['heading'],
                    'response_idx': r_idx,
                    'response_heading': response_arg['heading'],
                    'features': features
                })
        
        # Make predictions if we have pairs
        if not all_pairs:
            return jsonify({"links": [], "error": "No argument pairs to analyze."}), 400
            
        # Convert to numpy array for prediction
        X = np.array(all_pairs)
        
        # Get probabilities for positive class
        try:
            y_proba = model.predict_proba(X)[:, 1]
        except Exception as e:
            # Fallback to using semantic similarity as proxy for probability
            print(f"Error in prediction: {str(e)}. Using semantic similarity as fallback.")
            y_proba = np.array([p['features']['semantic_similarity'] for p in pair_details])
        
        # Create links with probabilities
        links_with_proba = []
        for i, p in enumerate(pair_details):
            links_with_proba.append({
                'moving_heading': p['moving_heading'],
                'response_heading': p['response_heading'],
                'probability': float(y_proba[i])
            })
        
        # Sort by probability in descending order
        links_with_proba.sort(key=lambda x: x['probability'], reverse=True)
        
        # Filter by threshold
        links_with_proba = [link for link in links_with_proba if link['probability'] >= threshold]
        
        # Post-processing: limit number of response arguments per moving argument
        final_links = []
        links_count = {}
        
        for link in links_with_proba:
            moving_heading = link['moving_heading']
            
            # Skip if we've already assigned max_links response arguments to this moving argument
            if moving_heading in links_count and links_count[moving_heading] >= max_links:
                continue
                
            # Add to final links
            final_links.append({
                'moving_heading': link['moving_heading'],
                'response_heading': link['response_heading'],
                'confidence': link['probability']
            })
            
            # Update counter
            if moving_heading not in links_count:
                links_count[moving_heading] = 1
            else:
                links_count[moving_heading] += 1
        
        return jsonify({
            'links': final_links,
            'model_info': {
                'threshold': threshold,
                'max_links_per_arg': max_links
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get information about the loaded model"""
    global model, feature_cols
    
    # Check if models are loaded
    if model is None:
        success = load_models()
        if not success:
            return jsonify({"error": "Failed to load models"}), 500
    
    # Get model information
    model_type = type(model).__name__
    
    # Try to get feature importances if available
    feature_importance = None
    if hasattr(model, 'named_steps') and hasattr(model.named_steps.get('classifier', None), 'coef_'):
        feature_importance = {}
        coefs = model.named_steps['classifier'].coef_[0]
        for i, feature in enumerate(feature_cols):
            feature_importance[feature] = float(coefs[i])
    elif hasattr(model, 'named_steps') and hasattr(model.named_steps.get('classifier', None), 'feature_importances_'):
        feature_importance = {}
        importances = model.named_steps['classifier'].feature_importances_
        for i, feature in enumerate(feature_cols):
            feature_importance[feature] = float(importances[i])
    
    return jsonify({
        'model_type': model_type,
        'feature_cols': feature_cols,
        'feature_importance': feature_importance
    })

# Load models at startup
if __name__ == '__main__':
    # Attempt to load models when the app starts
    load_models()
    app.run(debug=True, port=5000)