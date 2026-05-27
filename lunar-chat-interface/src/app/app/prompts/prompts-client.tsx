// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  Plus,
  FolderPlus,
  Folder,
  ScrollText,
  ChevronRight,
  Home,
  ArrowRight,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  createPrompt,
  deletePrompt,
  createDirectory,
  deleteDirectory,
  moveDirectory,
  movePrompt,
} from "./actions";
import { ListItem } from "@/components/list-item";
import { DeleteButton } from "@/components/delete-button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

interface DirectoryContents {
  directory: {
    id: string;
    name: string;
    parent_id: string | null;
  } | null;
  breadcrumb: {
    id: string;
    name: string;
    parent_id: string | null;
  }[];
  children: {
    id: string;
    name: string;
    type: "directory" | "prompt";
    created_at: string;
    updated_at: string;
  }[];
}

interface PromptsClientProps {
  initialContents: DirectoryContents;
  currentDirectoryId: string | null;
}

export function PromptsClient({
  initialContents,
  currentDirectoryId,
}: PromptsClientProps) {
  const [newPromptName, setNewPromptName] = useState("");
  const [newDirName, setNewDirName] = useState("");
  const [isCreatePromptOpen, setIsCreatePromptOpen] = useState(false);
  const [isCreateDirOpen, setIsCreateDirOpen] = useState(false);
  const [isMoveDialogOpen, setIsMoveDialogOpen] = useState(false);
  const [moveTarget, setMoveTarget] = useState<{
    id: string;
    type: "directory" | "prompt";
    name: string;
  } | null>(null);
  const [moveDestination, setMoveDestination] = useState<string>("__root__");
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  const { breadcrumb, children } = initialContents;

  const directories = children.filter((c) => c.type === "directory");

  const handleCreatePrompt = async () => {
    if (!newPromptName.trim()) return;
    startTransition(async () => {
      try {
        const created = await createPrompt(
          newPromptName.trim(),
          currentDirectoryId,
        );
        setNewPromptName("");
        setIsCreatePromptOpen(false);
        if (created && created.id) {
          router.push(`/app/prompts/${created.id}`);
        }
      } catch {
        toast.error("Failed to create prompt. Please try again.");
      }
    });
  };

  const handleCreateDirectory = async () => {
    if (!newDirName.trim()) return;
    startTransition(async () => {
      try {
        await createDirectory(newDirName.trim(), currentDirectoryId);
        setNewDirName("");
        setIsCreateDirOpen(false);
        router.refresh();
      } catch {
        toast.error("Failed to create directory. Please try again.");
      }
    });
  };

  const handleMove = async () => {
    if (!moveTarget) return;
    startTransition(async () => {
      try {
        const destination =
          moveDestination === "__root__" ? null : moveDestination;
        if (moveTarget.type === "directory") {
          await moveDirectory(moveTarget.id, destination);
        } else {
          await movePrompt(moveTarget.id, destination);
        }
        setIsMoveDialogOpen(false);
        setMoveTarget(null);
        setMoveDestination("__root__");
        router.refresh();
        toast.success("Moved successfully");
      } catch {
        toast.error("Failed to move item. Please try again.");
      }
    });
  };

  const openMoveDialog = (item: {
    id: string;
    type: "directory" | "prompt";
    name: string;
  }) => {
    setMoveTarget(item);
    setMoveDestination("__root__");
    setIsMoveDialogOpen(true);
  };

  return (
    <>
      <div className="flex justify-between">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-1 text-sm text-muted-foreground mb-2">
          <a
            href="/app/prompts"
            className="flex items-center gap-1 hover:text-foreground transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Root</span>
          </a>
          {breadcrumb.map((dir) => (
            <span key={dir.id} className="flex items-center gap-1">
              <ChevronRight className="w-4 h-4" />
              <a
                href={`/app/prompts/directory/${dir.id}`}
                className="hover:text-foreground transition-colors"
              >
                {dir.name}
              </a>
            </span>
          ))}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-2 justify-end">
          <Dialog open={isCreateDirOpen} onOpenChange={setIsCreateDirOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" disabled={isPending}>
                <FolderPlus className="w-4 h-4 mr-2" />
                New Directory
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Directory</DialogTitle>
                <DialogDescription>
                  Enter a name for the new directory.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="dirName">Directory Name</Label>
                  <Input
                    id="dirName"
                    value={newDirName}
                    onChange={(e) => setNewDirName(e.target.value)}
                    placeholder="Enter directory name..."
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleCreateDirectory();
                    }}
                    disabled={isPending}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDirOpen(false)}
                  disabled={isPending}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateDirectory}
                  disabled={isPending || !newDirName.trim()}
                >
                  {isPending ? "Creating..." : "Create Directory"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog
            open={isCreatePromptOpen}
            onOpenChange={setIsCreatePromptOpen}
          >
            <DialogTrigger asChild>
              <Button disabled={isPending}>
                <Plus className="w-4 h-4 mr-2" />
                New Prompt
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Prompt</DialogTitle>
                <DialogDescription>
                  Enter a name for your new prompt. You can edit the content
                  after creation.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="promptName">Prompt Name</Label>
                  <Input
                    id="promptName"
                    value={newPromptName}
                    onChange={(e) => setNewPromptName(e.target.value)}
                    placeholder="Enter prompt name..."
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleCreatePrompt();
                    }}
                    disabled={isPending}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsCreatePromptOpen(false)}
                  disabled={isPending}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreatePrompt}
                  disabled={isPending || !newPromptName.trim()}
                >
                  {isPending ? "Creating..." : "Create Prompt"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Directory contents */}
      <div>
        {children.map((item) => (
          <ListItem
            key={item.id}
            title={item.name}
            date={item.updated_at}
            href={
              item.type === "directory"
                ? `/app/prompts/directory/${item.id}`
                : `/app/prompts/${item.id}`
            }
            icon={
              item.type === "directory" ? (
                <Folder className="w-4 h-4 text-white" />
              ) : (
                <ScrollText className="w-4 h-4 text-white" />
              )
            }
            actions={
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-foreground"
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    openMoveDialog(item);
                  }}
                >
                  <ArrowRight className="h-4 w-4" />
                  <span className="sr-only">Move</span>
                </Button>
                <DeleteButton
                  title={`Delete ${item.type === "directory" ? "Directory" : "Prompt"}`}
                  description={`Are you sure you want to delete "${item.name}"?${item.type === "directory" ? " All contents will also be deleted." : ""} This action cannot be undone.`}
                  onDelete={() =>
                    item.type === "directory"
                      ? deleteDirectory(item.id)
                      : deletePrompt(item.id)
                  }
                  successMessage={`${item.type === "directory" ? "Directory" : "Prompt"} deleted successfully`}
                  errorMessage={`Failed to delete ${item.type === "directory" ? "directory" : "prompt"}`}
                />
              </div>
            }
          />
        ))}
      </div>

      {children.length === 0 && (
        <Card className="flex flex-col items-center justify-center py-12">
          <CardContent className="text-center">
            <h3 className="text-lg font-semibold mb-2">
              This directory is empty
            </h3>
            <p className="text-muted-foreground mb-4">
              Get started by creating a prompt or directory
            </p>
            <div className="flex gap-2 justify-center">
              <Button
                variant="outline"
                onClick={() => setIsCreateDirOpen(true)}
                disabled={isPending}
              >
                <FolderPlus className="w-4 h-4 mr-2" />
                New Directory
              </Button>
              <Button
                onClick={() => setIsCreatePromptOpen(true)}
                disabled={isPending}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Prompt
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Move Dialog */}
      <Dialog open={isMoveDialogOpen} onOpenChange={setIsMoveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Move &quot;{moveTarget?.name}&quot;</DialogTitle>
            <DialogDescription>
              Select the destination directory.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Destination</Label>
              <Select
                value={moveDestination}
                onValueChange={setMoveDestination}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select destination..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__root__">Root</SelectItem>
                  {directories
                    .filter((d) => d.id !== moveTarget?.id)
                    .map((d) => (
                      <SelectItem key={d.id} value={d.id}>
                        {d.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsMoveDialogOpen(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button onClick={handleMove} disabled={isPending}>
              {isPending ? "Moving..." : "Move"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
