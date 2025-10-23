load_pfp()

async function load_pfp() {
    if (sessionStorage.getItem('pfp')) {
        document.getElementById('pfp').src=`${sessionStorage.getItem('pfp')}`;
    } else {
        const data = await getPfp()
        if (data.success == true) {
            sessionStorage.setItem('pfp', data.pfp);
            document.getElementById('pfp').src=`${data.pfp}`;
        }
    }
}

async function getPfp() {
  const url = "/get_pfp/me";
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    return result
  } catch (error) {
    console.error(error.message);
  }
}

function logout() {
  sessionStorage.clear();
  window.location.href = '/logout';
}