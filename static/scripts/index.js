const inputForm = document.getElementById('dl-container');
const urlInput = document.getElementById('video-url');
const resolutionsSelect = document.getElementById('resolution');
const downloadButton = document.getElementById('download');
const placeholderOption = document.createElement('option');
placeholderOption.textContent = 'Enter a video URL to see the available resolutions';

var typingTimer;
urlInput.addEventListener('change', () => {
    clearTimeout(typingTimer);
    disableForm();
    if (inputForm.checkValidity()) {
        typingTimer = setTimeout(() => {
            const urlParams = new URLSearchParams();
            urlParams.append('url', urlInput.value);
            urlInput.disabled = true;

            fetch('/api/pre/resolutions?' + urlParams.toString())
                .then(res => {
                    urlInput.disabled = false;
                    resolutionsSelect.innerHTML = '';
                    
                    if (res.ok) {
                        enableForm();
                        urlInput.classList.remove('url-error');
                        urlInput.classList.add('url-success');
                        res.json()
                        .then(resolutions => {
                            for (const res of resolutions) {
                                    const option = document.createElement('option');
                                    option.value = option.textContent = res;
                                    resolutionsSelect.appendChild(option);
                                }
                                resolutionsSelect.disabled = false;
                            });
                        } else {
                            urlInput.classList.remove('url-success');
                            urlInput.classList.add('url-error');
                            resolutionsSelect.disabled = true;
                            resolutionsSelect.appendChild(placeholderOption);
                        }
                        
                    });
                }, 0);
            }
});

function disableForm() {
    downloadButton.disabled = true;
    
    urlInput.classList.remove('url-success');
    urlInput.classList.remove('url-error');
    urlInput.disabled = false;
    
    resolutionsSelect.innerHTML = ''
    resolutionsSelect.appendChild(placeholderOption);
    resolutionsSelect.disabled = true;
}

function enableForm() {
    downloadButton.disabled = false;
    urlInput.disabled = false;
    resolutionsSelect.disabled = false;
}