import {
  CompareIcon,
  DumbbellIcon,
  FamilyIcon,
  HistoryIcon,
  HomeIcon,
  QuestionCircleIcon,
  ScanIcon,
  SearchIcon,
  UserIcon,
} from "@/components/ui/icons";
import { DESTINATION_PATH, type Destination } from "./layouts";

type IconType = typeof HomeIcon;

/** Icon of each destination (labels are `nav.<destination>`). */
export const DESTINATION_ICON: Readonly<Record<Destination, IconType>> = {
  home: HomeIcon,
  scan: ScanIcon,
  history: HistoryIcon,
  family: FamilyIcon,
  protein: DumbbellIcon,
  compare: CompareIcon,
  search: SearchIcon,
  profile: UserIcon,
  how_we_score: QuestionCircleIcon,
};

export function destinationHref(locale: string, d: Destination): string {
  return `/${locale}/${DESTINATION_PATH[d]}`;
}
