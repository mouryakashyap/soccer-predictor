interface Props {
  edge: number;
}

export default function ValueBadge({ edge }: Props) {
  if (edge >= 0.1) {
    return (
      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800">
        Strong +{(edge * 100).toFixed(1)}%
      </span>
    );
  }
  if (edge >= 0.05) {
    return (
      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-yellow-100 text-yellow-800">
        Value +{(edge * 100).toFixed(1)}%
      </span>
    );
  }
  return (
    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-500">
      No value
    </span>
  );
}
