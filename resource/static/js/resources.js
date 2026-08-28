"use strict";


/*
|--------------------------------------------------------------------------
| CSRF Token
|--------------------------------------------------------------------------
*/

function getCSRFToken() {

    const csrfInput =
        document.querySelector(
            "[name=csrfmiddlewaretoken]"
        );

    return csrfInput
        ? csrfInput.value
        : getCookie("csrftoken");
}


function getCookie(name) {

    const cookies =
        document.cookie.split(";");

    for (const cookie of cookies) {

        const [key, value] =
            cookie.trim().split("=");

        if (key === name) {
            return decodeURIComponent(value);
        }
    }

    return null;
}


/*
|--------------------------------------------------------------------------
| Like Resource
|--------------------------------------------------------------------------
*/

const likeButton =
    document.querySelector("#likeButton");


if (likeButton) {

    likeButton.addEventListener(
        "click",
        async () => {

            const url =
                likeButton.dataset.url;

            likeButton.disabled = true;

            try {

                const response =
                    await fetch(
                        url,
                        {
                            method: "POST",

                            headers: {
                                "X-CSRFToken":
                                    getCSRFToken(),

                                "X-Requested-With":
                                    "XMLHttpRequest"
                            }
                        }
                    );


                const data =
                    await response.json();


                if (data.success) {

                    document.querySelector(
                        "#likeCount"
                    ).textContent =
                        data.likes;

                }

            } catch (error) {

                console.error(
                    "Like error:",
                    error
                );

                alert(
                    "Something went wrong."
                );

            } finally {

                likeButton.disabled = false;

            }

        }
    );

}


/*
|--------------------------------------------------------------------------
| Delete Resource
|--------------------------------------------------------------------------
*/

const deleteResource =
    document.querySelector(
        "#deleteResource"
    );


if (deleteResource) {

    deleteResource.addEventListener(
        "click",
        async () => {

            const confirmed =
                confirm(
                    "Are you sure you want to delete this resource?"
                );

            if (!confirmed) {
                return;
            }


            const url =
                deleteResource.dataset.url;


            try {

                const response =
                    await fetch(
                        url,
                        {
                            method: "POST",

                            headers: {
                                "X-CSRFToken":
                                    getCSRFToken(),

                                "X-Requested-With":
                                    "XMLHttpRequest"
                            }
                        }
                    );


                const data =
                    await response.json();


                if (data.success) {

                    window.location.href =
                        "/resources/";

                } else {

                    alert(
                        data.message ||
                        "Unable to delete resource."
                    );

                }

            } catch (error) {

                console.error(
                    "Delete error:",
                    error
                );

                alert(
                    "Something went wrong."
                );

            }

        }
    );

}


/*
|--------------------------------------------------------------------------
| Delete Comment
|--------------------------------------------------------------------------
*/

const deleteCommentButtons =
    document.querySelectorAll(
        ".delete-comment"
    );


deleteCommentButtons.forEach(
    (button) => {

        button.addEventListener(
            "click",
            async () => {

                const confirmed =
                    confirm(
                        "Delete this comment?"
                    );

                if (!confirmed) {
                    return;
                }


                const url =
                    button.dataset.url;


                try {

                    const response =
                        await fetch(
                            url,
                            {
                                method: "POST",

                                headers: {
                                    "X-CSRFToken":
                                        getCSRFToken(),

                                    "X-Requested-With":
                                        "XMLHttpRequest"
                                }
                            }
                        );


                    const data =
                        await response.json();


                    if (data.success) {

                        button
                            .closest(".border-b")
                            .remove();

                    } else {

                        alert(
                            data.message ||
                            "Unable to delete comment."
                        );

                    }

                } catch (error) {

                    console.error(
                        "Comment delete error:",
                        error
                    );

                }

            }
        );

    }
);


/*
|--------------------------------------------------------------------------
| Search Keyboard Shortcut
|--------------------------------------------------------------------------
*/

const searchInput =
    document.querySelector(
        'input[name="search"]'
    );


if (searchInput) {

    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.ctrlKey &&
                event.key.toLowerCase() === "k"
            ) {

                event.preventDefault();

                searchInput.focus();

            }

        }
    );

}