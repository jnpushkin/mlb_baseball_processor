"""Shared dialog focus, dismissal, and scroll behavior."""

CODE = r'''
const dialogStack = [];
let dialogBodyOverflow = '';
const Modal = ({ children, onClose, onPrevious, onNext, label, className }) => {
    const rootRef = useRef(null);
    const closeRef = useRef(onClose);
    closeRef.current = onClose;
    const navigationRef = useRef({ onPrevious, onNext });
    navigationRef.current = { onPrevious, onNext };
    useEffect(() => {
        const root = rootRef.current;
        const trigger = document.activeElement === document.body
            ? document.querySelector('[role="search"] input') : document.activeElement;
        if (!dialogStack.length) {
            dialogBodyOverflow = document.body.style.overflow;
            document.body.style.overflow = 'hidden';
        }
        dialogStack.push(root);
        root.style.zIndex = String(80 + dialogStack.length * 10);
        const isTop = () => dialogStack[dialogStack.length - 1] === root;
        const focusable = () => [...root.querySelectorAll('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
            .filter(el => el.getClientRects().length && !el.closest('[hidden], [inert]'));
        const focusFirst = () => (root.querySelector('[data-dialog-close]') || focusable()[0] || root).focus({ preventScroll: true });
        const onKey = (e) => {
            if (!isTop()) return;
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopImmediatePropagation();
                closeRef.current();
            } else if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && !e.target.closest('input, select, textarea, [contenteditable="true"]')) {
                const navigate = e.key === 'ArrowLeft' ? navigationRef.current.onPrevious : navigationRef.current.onNext;
                if (navigate) { e.preventDefault(); e.stopImmediatePropagation(); navigate(); }
            } else if (e.key === 'Tab') {
                const elements = focusable();
                const first = elements[0], last = elements[elements.length - 1];
                if (!first) { e.preventDefault(); root.focus(); }
                else if (e.shiftKey && (document.activeElement === first || !elements.includes(document.activeElement))) {
                    e.preventDefault(); last.focus();
                } else if (!e.shiftKey && (document.activeElement === last || !elements.includes(document.activeElement))) {
                    e.preventDefault(); first.focus();
                }
            }
        };
        const onFocus = (e) => { if (isTop() && !root.contains(e.target)) focusFirst(); };
        window.addEventListener('keydown', onKey, true);
        document.addEventListener('focusin', onFocus);
        focusFirst();
        return () => {
            const wasTop = isTop();
            dialogStack.splice(dialogStack.indexOf(root), 1);
            window.removeEventListener('keydown', onKey, true);
            document.removeEventListener('focusin', onFocus);
            if (!dialogStack.length) document.body.style.overflow = dialogBodyOverflow;
            if (wasTop && trigger?.isConnected) trigger.focus({ preventScroll: true });
        };
    }, []);
    return <div ref={rootRef} role="dialog" aria-modal="true" aria-label={label} tabIndex={-1}
        className={className} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
        {children}
    </div>;
};
'''
