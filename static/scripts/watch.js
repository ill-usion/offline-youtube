var videosProgress = {};
var registeredWatch = false;
var movedTopToBottom = false;
const curURL = new URL(window.location.href);
const videoID = curURL.searchParams.get("video");
const video = document.getElementById("video");
const videosList = document.getElementById("videos-list");
const videoContent = document.getElementById("video-content");
const watchedCheckbox = document.getElementById("video-watched");
const searchInput = document.getElementById("search");
const listVideos = document.getElementsByClassName("list-video");
const filterUnatchedCheckbox = document.getElementById("filter-unwatched");
const toggleListButton = document.getElementById("toggle-list");

reorderLayout();

toggleListButton.addEventListener("click", () => {
    if (videosList.style.display === "none") {
        videosList.style.display = "block";
        videoContent.style.gridColumn = "span 1";
        toggleListButton.style.opacity = "1";
        videoContent.classList.remove("full-view");
    } else {
        videosList.style.display = "none";
        videoContent.style.gridColumn = "span 2";
        toggleListButton.style.opacity = ".5";
        videoContent.classList.add("full-view");
    }
});

searchInput.addEventListener("input", () => {
    const searchTerm = searchInput.value.toLowerCase();

    for (let i = 0; i < listVideos.length; i++) {
        const videoTitle = listVideos[i]
            .querySelector("h2")
            .textContent.toLowerCase();

        if (videoTitle.includes(searchTerm)) {
            listVideos[i].style.display = "block";
        } else {
            listVideos[i].style.display = "none";
        }
    }
});

filterUnatchedCheckbox.addEventListener("input", () => {
    for (let i = 0; i < listVideos.length; i++) {
        if (filterUnatchedCheckbox.checked) {
            const videoWatched =
                listVideos[i].querySelector(".watch-status").textContent !==
                "✅";

            if (videoWatched) {
                listVideos[i].style.display = "block";
            } else {
                listVideos[i].style.display = "none";
            }
        } else {
            listVideos[i].style.display = "block";
        }
    }
});

document.addEventListener("keydown", (event) => {
    if (document.activeElement.tagName === "INPUT") return;

    switch (event.key) {
        case "f": {
            if (video.requestFullscreen) {
                video.requestFullscreen();
            } else if (video.mozRequestFullScreen) {
                video.mozRequestFullScreen();
            } else if (video.webkitRequestFullscreen) {
                video.webkitRequestFullscreen();
            } else if (video.msRequestFullscreen) {
                video.msRequestFullscreen();
            }
            break;
        }

        case "t": {
            toggleListButton.click();
            break;
        }
    }
});

function toggleWatched(id, mouseInteraction = true) {
    if (mouseInteraction) watchedCheckbox.checked = !watchedCheckbox.checked;

    fetch(`/api/watched/${id}`, {
        method: "post",
        body: JSON.stringify({
            state: !watchedCheckbox.checked,
        }),
    })
        .then((res) => {
            if (res.ok) {
                watchedCheckbox.checked = !watchedCheckbox.checked;
            }
        })
        .catch((err) =>
            alert(
                `Marking video as ${!watchedCheckbox.checked ? "watched" : "unwatched"
                } failed: ` + err
            )
        );
}

function deleteVideo(id) {
    fetch(`/api/video/${id}`, {
        method: "delete",
    })
        .then((res) => {
            if (res.ok) {
                window.location.href = "/watch";
            } else {
                res.text().then((text) => {
                    alert("Error deleting video: " + text);
                });
            }
        })
        .catch((err) => alert("Error deleting video: " + err));
}

function reorderLayout() {
    if (window.innerWidth <= 900 && !movedTopToBottom) {
        videosList.parentNode.appendChild(videosList);
        movedTopToBottom = true;
    }
    else if (window.innerWidth >= 900 && movedTopToBottom) {
        videoContent.parentNode.appendChild(videoContent);
        movedTopToBottom = false;
    }
}

window.addEventListener('resize', reorderLayout);

video.addEventListener("timeupdate", () => {
    if (
        !registeredWatch &&
        !watchedCheckbox.checked &&
        (video.currentTime / video.duration) >= 0.9
    ) {
        registeredWatch = true;
        toggleWatched(videoID, false);
    }
});

document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.videosProgress === undefined)
        return;

    videosProgress = JSON.parse(localStorage.videosProgress);

    if (videoID === null && videosProgress[videoID] === undefined)
        return;

    video.currentTime = videosProgress[videoID];
});

window.onbeforeunload = () => {
    if (videoID === null)
        return;
    videosProgress[videoID] = video.currentTime;
    localStorage.videosProgress = JSON.stringify(videosProgress);
};