export default function ClickWordmark({ className = "" }) {
  const classes = ["click-wordmark", className].filter(Boolean).join(" ");

  return (
    <div className={classes} aria-label="Click brand mark" role="img">
      <span className="click-wordmark-mark" aria-hidden="true">
        <span className="click-wordmark-mark-upper" />
        <span className="click-wordmark-mark-lower" />
      </span>
      <span className="click-wordmark-text">Click</span>
    </div>
  );
}
