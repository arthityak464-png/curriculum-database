import Badge from '../ui/Badge';
import { isVerified } from '../../lib/curriculum';

export default function VerificationBadge({ item, verified }) {
  const ok = verified ?? isVerified(item);
  return (
    <Badge tone={ok ? 'ok' : 'warn'} dot>
      {ok ? 'อนุมัติแล้ว' : 'รอตรวจทาน'}
    </Badge>
  );
}
