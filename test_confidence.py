import requests
import json

def test_ai_confidence():
    data = {'message': 'What is the weather like for sailing today?'}
    
    try:
        response = requests.post('http://localhost:8000/api/ai/public_chat', json=data, timeout=15)
        print(f'HTTP Status: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print(f'Response keys: {list(result.keys())}')
            
            confidence = result.get('confidence')
            if confidence is not None:
                print(f'✅ AI Response Confidence: {confidence * 100:.1f}%')
            else:
                print('❌ No confidence field in response')
                
            response_text = result.get('response', '')
            print(f'Response preview: {response_text[:100]}...')
            
        else:
            print(f'Error response: {response.text}')
            
    except Exception as e:
        print(f'Connection error: {str(e)}')

if __name__ == "__main__":
    test_ai_confidence()