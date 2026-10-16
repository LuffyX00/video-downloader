export default function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div role="alert" className="mt-4 rounded-md border-l-4 border-danger bg-danger-tint px-4 py-3 text-sm text-danger">
      {message}
    </div>
  );
}
