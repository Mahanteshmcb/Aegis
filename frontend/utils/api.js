const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export const loginAPI = async (email, password) => {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // Clean, trim, and send ONLY what is needed
      body: JSON.stringify({ 
        email: email.trim().toLowerCase(), 
        password: password 
      }), 
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Authentication failed');
    }

    return await response.json(); 
  } catch (error) {
    console.error("API Error during login:", error);
    throw error;
  }
};