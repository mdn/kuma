//@flow

// Our current build pipeline arranges to have a suitable gettext()
// function installed as a global. But for webpack, flow and other
// tools, we need a version of the function that we can statically
// import into modules. This version calls the globally defined
// gettext() if it exists, and otherwise just returns the passed
// string without translation.
export default function gettext(english: string): string {
    try {
        let translation = window.gettext(english);
        return (translation: string);
    } catch (e) {
        return english;
    }
}
