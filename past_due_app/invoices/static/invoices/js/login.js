export async function login() {
  try {
      const response = await fetch("login-to-ksef/", {
          method: 'GET',
          headers: {
              'Accept': 'application/json'
          }
      });

      if (!response.ok) {
          throw new Error(`API Error (${response.status}): ${response.statusText}`);
      }

      return await response.json();

  } catch (error) {
      console.error('API Error:', error.message);
      return null;
  }
}